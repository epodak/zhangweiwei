use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;
use std::sync::Arc;
use tokio;
use rayon::prelude::*;
use env_logger;
use std::io::{self, BufRead};
use aho_corasick::AhoCorasick;

#[derive(Debug, Serialize, Deserialize)]
struct SubtitleItem {
    timestamp: String,
    similarity: f64,
    text: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct SearchResult {
    filename: String,
    timestamp: String,
    similarity: f64,
    text: String,
    match_ratio: f64,
    exact_match: bool,
}

#[derive(Debug, Serialize, Deserialize)]
struct SearchResponse {
    status: String,
    data: Vec<SearchResult>,
    count: usize,
    folder: String,
    max_results: String,
    message: Option<String>,
    suggestions: Option<Vec<String>>,
}

#[derive(Debug, Deserialize)]
struct SearchParams {
    query: String,
    #[serde(default = "default_min_ratio")]
    min_ratio: f64,
    #[serde(default = "default_min_similarity")]
    min_similarity: f64,
    max_results: Option<i32>,
}

fn default_min_ratio() -> f64 { 50.0 }
fn default_min_similarity() -> f64 { 0.0 }

fn lcs_ratio(str1: &str, str2: &str) -> f64 {
    let str1_lower = str1.to_lowercase();
    let str2_lower = str2.to_lowercase();
    
    if str1_lower.is_empty() || str2_lower.is_empty() {
        return 0.0;
    }

    let str1_chars: Vec<char> = str1_lower.chars().collect();
    let str2_chars: Vec<char> = str2_lower.chars().collect();
    let m = str1_chars.len();
    let n = str2_chars.len();
    
    // 使用动态规划计算LCS
    let mut dp = vec![vec![0; n + 1]; m + 1];
    
    for i in 1..=m {
        for j in 1..=n {
            if str1_chars[i-1] == str2_chars[j-1] {
                dp[i][j] = dp[i-1][j-1] + 1;
            } else {
                dp[i][j] = dp[i-1][j].max(dp[i][j-1]);
            }
        }
    }
    
    let lcs_length = dp[m][n];
    (lcs_length as f64 / m as f64) * 100.0
}

fn find_non_overlapping_matches(text: &str, pattern: &str) -> Vec<(usize, usize)> {
    let text = text.to_lowercase();
    let pattern = pattern.to_lowercase();
    
    let mut matches = Vec::new();
    let mut start_pos = 0;
    
    while let Some(pos) = text[start_pos..].find(&pattern) {
        let abs_pos = start_pos + pos;
        matches.push((abs_pos, abs_pos + pattern.len() - 1));
        start_pos = abs_pos + 1;
    }
    
    matches
}

fn multi_word_lcs_ratio(query_words: &[String], text: &str) -> f64 {
    let text = text.to_lowercase();
    let total_query_length: usize = query_words.iter().map(|w| w.len()).sum();
    
    let mut used_chars = vec![false; text.len()];
    let mut total_matched = 0;
    
    for word in query_words {
        let word_lower = word.to_lowercase();
        let mut found_match = false;
        
        let mut start_pos = 0;
        while let Some(pos) = text[start_pos..].find(&word_lower) {
            let abs_pos = start_pos + pos;
            let end_pos = abs_pos + word_lower.len();
            
            let mut can_use = true;
            for i in abs_pos..end_pos {
                if used_chars[i] {
                    can_use = false;
                    break;
                }
            }
            
            if can_use {
                for i in abs_pos..end_pos {
                    used_chars[i] = true;
                }
                total_matched += word_lower.len();
                found_match = true;
                break;
            }
            
            start_pos = abs_pos + 1;
        }
        
        if !found_match {
            continue;
        }
    }
    
    (total_matched as f64 / total_query_length as f64) * 100.0
}

async fn search_json_files(
    folder_path: &str,
    query: &str,
    min_ratio: f64,
    min_similarity: f64,
    max_results: Option<i32>,
) -> Vec<(String, String, f64, String, f64)> {
    let query = query.to_lowercase();
    let has_spaces = query.contains(' ') || query.contains("%20");
    let query_words: Vec<String> = if has_spaces {
        query.replace("%20", " ")
            .split_whitespace()
            .map(String::from)
            .collect()
    } else {
        vec![query.clone()]
    };

    let entries: Vec<_> = match fs::read_dir(folder_path) {
        Ok(entries) => entries.filter_map(Result::ok)
            .filter(|e| e.path().extension().map_or(false, |ext| ext == "json"))
            .collect(),
        Err(_) => return Vec::new(),
    };

    let results: Vec<_> = entries.par_iter()
        .filter_map(|entry| {
            let filename = entry.file_name().to_string_lossy().into_owned();
            
            let content = fs::read_to_string(entry.path()).ok()?;
            let data: Vec<SubtitleItem> = serde_json::from_str(&content).ok()?;

            let file_results: Vec<_> = data.par_iter()
                .filter(|item| item.similarity >= min_similarity)
                .filter_map(|item| {
                    let match_ratio = if has_spaces {
                        multi_word_lcs_ratio(&query_words, &item.text)
                    } else {
                        lcs_ratio(&query, &item.text)
                    };

                    if match_ratio >= min_ratio {
                        Some((filename.clone(), item.timestamp.clone(), item.similarity, item.text.clone(), match_ratio))
                    } else {
                        None
                    }
                })
                .collect();

            if file_results.is_empty() {
                None
            } else {
                Some(file_results)
            }
        })
        .flatten()
        .collect();

    let mut results = results;
    results.par_sort_unstable_by(|a, b| {
        let a_contains_all = query_words.iter().all(|word| a.3.to_lowercase().contains(word));
        let b_contains_all = query_words.iter().all(|word| b.3.to_lowercase().contains(word));
        b.4.partial_cmp(&a.4)
            .unwrap()
            .then(b_contains_all.cmp(&a_contains_all))
    });

    if let Some(max) = max_results {
        results.truncate(max as usize);
    }

    results
}

fn parse_args() -> SearchParams {
    let mut params = SearchParams {
        query: String::new(),
        min_ratio: default_min_ratio(),
        min_similarity: default_min_similarity(),
        max_results: None,
    };

    let input = io::stdin().lock().lines().next()
        .expect("无法读取输入")
        .expect("无法解析输入");

    for pair in input.split('&') {
        let mut parts = pair.splitn(2, '=');
        if let (Some(key), Some(value)) = (parts.next(), parts.next()) {
            match key {
                "query" => params.query = value.to_string(),
                "min_ratio" => params.min_ratio = value.parse().unwrap_or(50.0),
                "min_similarity" => params.min_similarity = value.parse().unwrap_or(0.0),
                "max_results" => params.max_results = value.parse().ok(),
                _ => {}
            }
        }
    }
    params
}

#[tokio::main]
async fn main() {
    env_logger::init();
    
    let default_folder = "subtitle";
    if !Path::new(default_folder).is_dir() {
        println!("{{\"status\": \"error\", \"message\": \"默认的'subtitle'文件夹不存在: {}\"}}", default_folder);
        return;
    }

    let params = parse_args();

    if params.query.is_empty() {
        println!("{{\"status\": \"error\", \"message\": \"搜索关键词不能为空\"}}");
        return;
    }

    if !(0.0..=100.0).contains(&params.min_ratio) {
        println!("{{\"status\": \"error\", \"message\": \"最小匹配率必须在0-100之间\"}}");
        return;
    }

    if !(0.0..=1.0).contains(&params.min_similarity) {
        println!("{{\"status\": \"error\", \"message\": \"最小原始相似度必须在0-1之间\"}}");
        return;
    }

    if let Some(max_results) = params.max_results {
        if max_results <= 0 {
            println!("{{\"status\": \"error\", \"message\": \"最大返回结果数量必须大于0\"}}");
            return;
        }
    }

    let results = search_json_files(
        default_folder,
        &params.query,
        params.min_ratio,
        params.min_similarity,
        params.max_results,
    ).await;

    let query_words: Vec<String> = params.query.replace("%20", " ")
        .split_whitespace()
        .map(String::from)
        .collect();

    let response = if !results.is_empty() {
        results.into_iter()
            .map(|(filename, timestamp, similarity, text, match_ratio)| {
                let search_result = SearchResult {
                    filename,
                    timestamp,
                    similarity,
                    text: text.clone(),
                    match_ratio,
                    exact_match: query_words.iter()
                        .all(|word| text.to_lowercase().contains(&word.to_lowercase())),
                };
                serde_json::to_string(&search_result).unwrap()
            })
            .collect::<Vec<String>>()
            .join("\n")
    } else {
        serde_json::to_string(&SearchResponse {
            status: "success".to_string(),
            data: vec![],
            count: 0,
            folder: default_folder.to_string(),
            max_results: params.max_results.map_or("unlimited".to_string(), |m| m.to_string()),
            message: Some(format!("未找到与 '{}' 匹配的结果", params.query)),
            suggestions: Some(vec![
                "检查输入是否正确".to_string(),
                format!("尝试降低最小匹配率（当前：{}%）", params.min_ratio),
                format!("尝试降低最小原始相似度（当前：{}）", params.min_similarity),
                "尝试使用更简短的关键词".to_string(),
            ]),
        }).unwrap()
    };

    println!("{}", response);
} 