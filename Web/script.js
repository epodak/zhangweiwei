// 先加载 mapping.json 文件
async function loadMapping() {
    try {
        const response = await fetch('./mapping.json');
        if (!response.ok) throw new Error("无法加载 mapping.json");
        return await response.json();
    } catch (error) {
        console.error(error);
        return {}; // 如果加载失败，返回一个空对象
    }
}

// 应用状态管理
const AppState = {
    isSearching: false,
    randomStringDisplayed: false
};

// 配置常量
const CONFIG = {
    randomStrings: ["探索VV的开源世界", "为东大助力", "搜索你想要的内容"],
    apiBaseUrl: 'https://vv-indol.vercel.app'
};

// UI 控制器
class UIController {
    static updateSearchFormPosition(isSearching) {
        const searchForm = document.getElementById('searchForm');
        if (isSearching) {
            searchForm.classList.add('searching');
        } else {
            searchForm.classList.remove('searching');
        }
    }

    static showRandomString() {
        if (!AppState.randomStringDisplayed) {
            const randomStringDisplay = document.getElementById('randomStringDisplay');
            const randomIndex = Math.floor(Math.random() * CONFIG.randomStrings.length);
            randomStringDisplay.textContent = CONFIG.randomStrings[randomIndex];
            AppState.randomStringDisplayed = true;
        }
    }

    static clearRandomString() {
        document.getElementById('randomStringDisplay').textContent = '';
        AppState.randomStringDisplayed = false;
    }

}

// 搜索控制器
class SearchController {
    static async performSearch(query, minRatio, minSimilarity, maxResults) {
        const url = `${CONFIG.apiBaseUrl}/search?query=${encodeURIComponent(query)}&min_ratio=${minRatio}&min_similarity=${minSimilarity}&max_results=${maxResults}`;
        
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error("网络请求失败");
            return await response.json();
        } catch (error) {
            console.error('搜索错误:', error);
            throw error;
        }
    }

    static validateSearchInput(query) {
        return query.trim() !== "";
    }
}

// 处理搜索的主函数
async function handleSearch(mapping) {
    const query = document.getElementById('query').value.trim();
    const minRatio = document.getElementById('minRatio').value;
    const minSimilarity = document.getElementById('minSimilarity').value;
    const maxResults = document.getElementById('maxResults').value;

    if (!SearchController.validateSearchInput(query)) {
        alert("请输入搜索关键词！");
        return;
    }

    try {
        startLoadingBar();
        UIController.showRandomString();
        UIController.updateSearchFormPosition(true);
        document.getElementById('results').innerHTML = '';

        const data = await SearchController.performSearch(query, minRatio, minSimilarity, maxResults);
        
        displayResults(data);
    } catch (error) {
        console.error('搜索失败:', error);
        document.getElementById('results').innerHTML = '<div class="result-card">搜索失败，请稍后重试</div>';
    } finally {

        completeLoadingBar();
        UIController.clearRandomString();
        UIController.updateSearchFormPosition(false);
    }
}

async function initializeApp() {
    try {
        const mapping = await loadMapping();
        
        document.getElementById('searchForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            if (AppState.isSearching) return;
            
            AppState.isSearching = true;
            try {
                await handleSearch(mapping);
            } finally {
                AppState.isSearching = false;
            }
        });

        // 监听回车键 (Enter) 事件，防止重复提交
        document.getElementById('query').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault(); // 阻止浏览器默认提交
                if (AppState.isSearching) return; // 如果正在搜索，忽略回车
                document.getElementById('searchForm').dispatchEvent(new Event('submit'));
            }
        });

        document.getElementById('refreshDiv').addEventListener('click', function() {
            location.reload(); // 刷新页面
        });

        
    } catch (error) {
        console.error('初始化失败:', error);
    }
}

// 启动应用
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();

    const toggleButton = document.getElementById('toggleAdvancedOptions');
    const advancedOptions = document.getElementById('advancedOptions');
    
    toggleButton.addEventListener('click', () => {
        const isExpanded = advancedOptions.classList.contains('show');
        
        // 切换状态前先设置最大高度
        if (!isExpanded) {
            // 临时移除 transition 以获取实际高度
            advancedOptions.style.transition = 'none';
            advancedOptions.classList.add('show');
            const height = advancedOptions.scrollHeight;
            advancedOptions.classList.remove('show');
            
            // 重新启用 transition
            void advancedOptions.offsetHeight; // 触发重排
            advancedOptions.style.transition = '';
            advancedOptions.style.maxHeight = height + 'px';
            advancedOptions.classList.add('show');
        } else {
            advancedOptions.style.maxHeight = '0';
            advancedOptions.classList.remove('show');
        }
        
        toggleButton.classList.toggle('active');
        toggleButton.setAttribute('aria-expanded', !isExpanded);
    });
});

// 显示搜索结果
function displayResults(data) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '';

    if (data.status !== 'success' || data.count === 0) {
        resultsDiv.innerHTML = '<div class="result-card">未找到匹配结果</div>';
        return;
    }

    data.data.forEach(result => {
        const episodeMatch = result.filename.match(/\[P(\d+)\]/);
        const timeMatch = result.timestamp.match(/^(\d+)m(\d+)s$/);
        
        let imageUrl = '';
        if (episodeMatch && timeMatch) {
            const episodeNum = parseInt(episodeMatch[1], 10);
            const totalSeconds = parseInt(timeMatch[1]) * 60 + parseInt(timeMatch[2]);
            imageUrl = `frames/${episodeNum}/frame_${totalSeconds}.webp`;
        }

        const cleanFilename = result.filename
            .replace(/\[P(\d+)\].*?\s+/, 'P$1 ')
            .replace(/\.json$/, '')
            .trim();

        const card = document.createElement('div');
        card.className = 'result-card';
        
        // 修改图片处理逻辑
        const cardContent = `
            <div class="result-content">
                <h3><span class="tag">${cleanFilename.match(/P\d+/)}</span>${cleanFilename.replace(/P\d+/, '').trim()}</h3>
                <p class="result-text">${result.text}</p>
                <p class="result-meta">${result.timestamp} · 匹配度 ${parseFloat(result.match_ratio).toFixed(1)}% · 相似度 ${(result.similarity * 100).toFixed(1)}%</p>
            </div>
        `;

        if (imageUrl) {
            const img = new Image();
            img.src = imageUrl;
            img.className = 'preview-frame';
            img.loading = 'lazy';
            
            img.onerror = () => {
                card.innerHTML = cardContent; // 加载失败时只显示内容
            };
            
            img.onload = () => {
                card.innerHTML = img.outerHTML + cardContent; // 加载成功时显示图片和内容
            };
        }
        
        card.innerHTML = cardContent; // 先显示内容

        card.addEventListener('click', () => handleCardClick(result));
        resultsDiv.appendChild(card);
    });
}

// 根据 filename 查找对应的播放 URL
function getEpisodeUrl(filename) {
    for (let key in mapping) {
        if (mapping[key] === filename) {
            return key;
        }
    }
    return null; // 没有找到对应的 URL
}

/**
 * 启动进度条，预计 3 秒走完
 */
function startLoadingBar() {
    const loadingBar = document.getElementById('loadingBar');
    loadingBar.style.width = "0%";
    loadingBar.style.display = "block";
    
    let progress = 0;
    loadingBar.interval = setInterval(() => {
        progress += 2; // 加快进度条速度
        if (progress > 90) progress = 90; // 最多到90%
        loadingBar.style.width = `${progress}%`;
    }, 30);
}

/**
 * 提前完成进度条并隐藏
 */
function completeLoadingBar() {
    const loadingBar = document.getElementById('loadingBar');
    clearInterval(loadingBar.interval);
    loadingBar.style.width = "100%";
    
    setTimeout(() => {
        loadingBar.style.display = "none";
        loadingBar.style.width = "0%";
    }, 300);
}