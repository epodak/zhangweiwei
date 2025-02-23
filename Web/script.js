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

// 当 mapping.json 加载完成后，执行以下代码
loadMapping().then(mapping => {
    let isSearching = false;  // 用于判断是否正在搜索

    document.getElementById('searchForm').addEventListener('submit', async (e) => {
        if (isSearching) return; // 如果正在搜索，忽略这次提交
        isSearching = true;  // 设置搜索状态为正在搜索
        e.preventDefault(); // 阻止默认提交行为
        startLoadingBar();  // 显示进度条
        showRandomString(); // 显示一次随机字符串
        searchQuery(); // 执行搜索逻辑
    });

    // 监听回车键 (Enter) 事件，防止重复提交
    document.getElementById('query').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault(); // 阻止浏览器默认提交
            if (isSearching) return; // 如果正在搜索，忽略回车
            document.getElementById('searchForm').dispatchEvent(new Event('submit'));
        }
    });

    // 随机字符串数组
    const randomStrings = ["看看项目的GitHub！", "成为VV的开源用户！", "帮助东大的可怜儿童！"];

    document.getElementById('refreshDiv').addEventListener('click', function() {
        location.reload(); // 刷新页面
    });

    // 显示随机字符串的函数
    let randomStringDisplayed = false;
    function showRandomString() {
        if (!randomStringDisplayed) {
            const randomStringDisplay = document.getElementById('randomStringDisplay');
            const randomIndex = Math.floor(Math.random() * randomStrings.length);
            randomStringDisplay.innerText = randomStrings[randomIndex];
            randomStringDisplayed = true;
        }
    }

    // 搜索逻辑封装在单独函数
    async function searchQuery() {
        const query = document.getElementById('query').value.trim();
        const minRatio = document.getElementById('minRatio').value;
        const minSimilarity = document.getElementById('minSimilarity').value;
        const maxResults = document.getElementById('maxResults').value;

        // 如果搜索框为空，则不进行搜索
        if (query === "") {
            alert("请输入搜索关键词！");
            isSearching = false; // 搜索结束，恢复为非搜索状态
            return;
        }

        // 让搜索框向上移动
        moveSearchFormUp();

        // 清空结果区，确保每次开始新搜索时不会显示上次的结果
        document.getElementById('results').innerHTML = '';

        // 生成 API URL
        const url = `https://vvapi.cicada000.work/search?query=${encodeURIComponent(query)}&min_ratio=${minRatio}&min_similarity=${minSimilarity}&max_results=${maxResults}`;

        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error("网络请求失败");

            const data = await response.json();
            completeLoadingBar(); // 提前完成进度条
            stopRandomString(); // 停止显示随机字符串
            displayResults(data);
        } catch (error) {
            console.error('Error:', error);
            completeLoadingBar();
            stopRandomString(); // 停止显示随机字符串
            document.getElementById('results').innerHTML = '<p>搜索失败，请稍后重试</p>';
        } finally {
            isSearching = false;  // 搜索完成后恢复为非搜索状态
        }
    }

    // 让搜索框从居中移动到顶部
    function moveSearchFormUp() {
        const searchForm = document.getElementById('searchForm');
        if (searchForm.classList.contains('centered')) {
            searchForm.classList.remove('centered');
            searchForm.classList.add('top');
        }

        // 让结果显示
        document.getElementById('results').style.display = 'block';
    }

    // 显示搜索结果
    function displayResults(data) {
        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = ''; // 清空旧的搜索结果

        if (data.status !== 'success' || data.count === 0) {
            resultsDiv.innerHTML = '<p>未找到匹配结果</p>';
            return;
        }

        data.data.forEach(result => {
            const card = document.createElement('div');
            card.className = 'result-card';
            card.innerHTML = `
                <h3>${result.filename}</h3>
                <p>匹配文本: <span class="highlight">${result.text}</span></p>
                <p>时间戳: ${result.timestamp}</p>
                <p>匹配度: ${result.match_ratio}%</p>
                <p>相似度: ${(result.similarity * 100).toFixed(1)}%</p>
                <p>精确匹配: ${result.exact_match ? '是' : '否'}</p>
            `;

            // 添加点击事件，跳转到相应的 B站链接
            card.addEventListener('click', () => {
                const timestamp = result.timestamp;
            
                // 使用正则表达式来匹配分钟和秒数的格式（例如 "21m50s"）
                const match = timestamp.match(/^(\d+)m(\d+)s$/);
            
                if (match) {
                    const minutes = parseInt(match[1], 10);  // 解析分钟部分
                    const seconds = parseInt(match[2], 10);  // 解析秒数部分
                    const totalSeconds = minutes * 60 + seconds; // 计算总秒数
            
                    // 获取映射中的 URL
                    const episodeUrl = getEpisodeUrl(result.filename);
                    if (episodeUrl) {
                        // 拼接完整的 B站播放链接
                        const videoUrl = `https://www.bilibili.com${episodeUrl}?share_source=copy_web&t=${totalSeconds}`;
                        window.open(videoUrl, '_blank'); 
                    } else {
                        alert("找不到对应的播放链接");
                    }
                } else {
                    alert("时间戳格式错误，请检查！"); // 如果格式不匹配，提示错误
                }
            });

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
     * 启动进度条，预计 7 秒走完
     */
    function startLoadingBar() {
        const loadingBar = document.getElementById('loadingBar');
        loadingBar.style.width = "0%";
        loadingBar.style.display = "block";
        
        let progress = 0;
        loadingBar.interval = setInterval(() => {
            progress += 1; // 每次增加 1%
            loadingBar.style.width = `${progress}%`;

            // 如果走完 100%，则隐藏
            if (progress >= 100) {
                clearInterval(loadingBar.interval);
                loadingBar.style.display = "none";
            }
        }, 70); // 7 秒走完 (70ms * 100 = 7000ms)
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
        }, 500); // 0.5秒后隐藏
    }

    /**
     * 停止随机字符串的显示
     */
    function stopRandomString() {
        document.getElementById('randomStringDisplay').innerText = ''; // 清空显示的字符串
    }

}).catch(error => {
    console.error('加载 mapping.json 失败:', error);
});