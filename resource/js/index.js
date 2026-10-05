console.log("index.js - 带 fallback 的最终版");

// 分类映射（后端已支持“推荐”→全量列表的映射）
const categoryMap = {
    "推荐": "推荐",
    "日记": "日记",
    "周记": "周记",
    "备忘录": "备忘录",
    "阅读笔记": "阅读笔记",
    "影后观感": "影后观感",
};

let currentPage = 1;
let currentDisplayCategory = "推荐";
let currentApiCategory = categoryMap["推荐"];
let isLoading = false;
let pendingUrl = null;
let scrollTimer = null;
//搜索模式相关变量
let currentKeyword = null;
let isSearchMode = false;

function buildUrl(page, apiCategory, startNum) {
    if (isSearchMode && currentKeyword) {
        // 搜索模式：携带 keyword，忽略分类
        return `?keyword=${encodeURIComponent(currentKeyword)}&page=${page}&start_num=${startNum}&scroll=1`;
    } else {
        // 正常分类模式（参数名与后端一致：article_type）
        return `?page=${page}&article_type=${encodeURIComponent(apiCategory)}&start_num=${startNum}&scroll=1`;
    }
}

function isNearBottom() {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
    const clientHeight = window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight || 0;
    const scrollHeight = document.documentElement.scrollHeight || document.body.scrollHeight || 0;
    return scrollTop + clientHeight + 200 >= scrollHeight;
}

async function loadNextPage() {
    if (isLoading) return;
    if (window.startNum === window.endNum && window.startNum !== 0) {
        document.querySelector(".load-more").innerHTML = "没有更多内容了";
        return;
    }
    const nextPage = currentPage + 1;
    const startNum = window.endNum || 0;
    const url = buildUrl(nextPage, currentApiCategory, startNum);
    if (pendingUrl === url) return;
    pendingUrl = url;
    isLoading = true;
    console.log("加载下一页:", url);
    try {
        const res = await fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } });
        const html = await res.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, "text/html");
        let newRows = doc.querySelectorAll(".article-row");
        if (newRows.length === 0) {
            document.querySelector(".load-more").innerHTML = "没有更多内容了";
            isLoading = false;
            pendingUrl = null;
            return;
        }
        let newStart = null, newEnd = null;
        const scripts = doc.querySelectorAll("script");
        for (let sc of scripts) {
            const text = sc.textContent || sc.innerText;
            if (text.includes("window.startNum")) {
                const sm = text.match(/window\.startNum\s*=\s*(\d+)/);
                const em = text.match(/window\.endNum\s*=\s*(\d+)/);
                if (sm) newStart = parseInt(sm[1]);
                if (em) newEnd = parseInt(em[1]);
                break;
            }
        }
        if (newStart !== null && newEnd !== null) {
            window.startNum = newStart;
            window.endNum = newEnd;
        } else {
            window.endNum = (window.endNum || 0) + newRows.length;
        }
        const container = document.querySelector(".article-inner");
        const loadMoreDiv = document.querySelector(".load-more");
        newRows.forEach(row => container.insertBefore(row, loadMoreDiv));
        currentPage = nextPage;
        if (window.startNum === window.endNum && window.startNum !== 0) {
            document.querySelector(".load-more").innerHTML = "没有更多内容了";
        } else {
            document.querySelector(".load-more").innerHTML = "下滑加载更多内容";
        }
        isLoading = false;
        pendingUrl = null;
    } catch (err) {
        console.error("加载失败:", err);
        document.querySelector(".load-more").innerHTML = "加载失败，请重试";
        isLoading = false;
        pendingUrl = null;
    }
}

async function switchCategory(displayCategory) {
	// 搜索模式下点击分类，清除搜索并重新加载该分类
	if (isSearchMode) {
	    const url = new URL(window.location.href);
	    url.searchParams.delete("keyword");
	    window.location.href = url.toString();
	    return;
	}
    const apiCategory = categoryMap[displayCategory];
    if (!apiCategory) {
        console.error("未知分类:", displayCategory);
        return;
    }
    if (currentApiCategory === apiCategory && currentDisplayCategory === displayCategory) return;
    currentDisplayCategory = displayCategory;
    currentApiCategory = apiCategory;
    currentPage = 1;
    isLoading = false;
    pendingUrl = null;
    let url = buildUrl(1, apiCategory, 0);
    console.log("切换分类:", url);
    try {
        let res = await fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } });
        let html = await res.text();
        let parser = new DOMParser();
        let doc = parser.parseFromString(html, "text/html");
        let newRows = doc.querySelectorAll(".article-row");
        // fallback: 如果映射后无数据，尝试用原始显示名称再请求一次
        if (newRows.length === 0 && apiCategory !== displayCategory) {
            console.log(`映射 "${apiCategory}" 无数据，尝试原始分类 "${displayCategory}"`);
            const fallbackUrl = buildUrl(1, displayCategory, 0);
            res = await fetch(fallbackUrl, { headers: { "X-Requested-With": "XMLHttpRequest" } });
            html = await res.text();
            parser = new DOMParser();
            doc = parser.parseFromString(html, "text/html");
            newRows = doc.querySelectorAll(".article-row");
            if (newRows.length > 0) {
                currentApiCategory = displayCategory; // 后续滚动使用原始分类
            }
        }
        const container = document.querySelector(".article-inner");
        const loadMoreDiv = document.querySelector(".load-more");
        const oldRows = container.querySelectorAll(".article-row");
        oldRows.forEach(row => row.remove());
        if (newRows.length === 0) {
            document.querySelector(".load-more").innerHTML = "暂无内容";
            window.startNum = 0;
            window.endNum = 0;
            return;
        }
        newRows.forEach(row => container.insertBefore(row, loadMoreDiv));
        let newStart = null, newEnd = null;
        const scripts = doc.querySelectorAll("script");
        for (let sc of scripts) {
            const text = sc.textContent || sc.innerText;
            if (text.includes("window.startNum")) {
                const sm = text.match(/window\.startNum\s*=\s*(\d+)/);
                const em = text.match(/window\.endNum\s*=\s*(\d+)/);
                if (sm) newStart = parseInt(sm[1]);
                if (em) newEnd = parseInt(em[1]);
                break;
            }
        }
        if (newStart !== null && newEnd !== null) {
            window.startNum = newStart;
            window.endNum = newEnd;
        } else {
            window.startNum = 0;
            window.endNum = newRows.length;
        }
        if (window.startNum === window.endNum && window.startNum !== 0) {
            document.querySelector(".load-more").innerHTML = "没有更多内容了";
        } else {
            document.querySelector(".load-more").innerHTML = "下滑加载更多内容";
        }
        // 更新左侧菜单高亮
        const menuDivs = document.querySelectorAll('.left-menu > div');
        menuDivs.forEach(div => {
            const a = div.querySelector('a');
            if (a && a.innerText.trim() === displayCategory) {
                div.className = 'selected';
            } else {
                div.className = 'no-selected';
            }
        });
        history.pushState(null, "", `?article_type=${encodeURIComponent(displayCategory)}&page=1`);
        window.scrollTo(0, 0);
    } catch (err) {
        console.error("切换分类失败:", err);
    }
}

function handleScroll() {
    if (scrollTimer) clearTimeout(scrollTimer);
    scrollTimer = setTimeout(() => {
        if (isNearBottom()) loadNextPage();
    }, 200);
}

function bindCategoryClicks() {
    const leftMenu = document.querySelector(".left-menu");
    if (!leftMenu) return;
    leftMenu.addEventListener("click", (e) => {
        let target = e.target;
        while (target && target !== leftMenu) {
            if (target.tagName === "A") {
                e.preventDefault();
                const cat = target.innerText.trim();
                if (cat) {
                    console.log("点击分类:", cat);
                    switchCategory(cat);
                }
                return;
            }
            target = target.parentNode;
        }
    });
}

function init() {
    const params = new URLSearchParams(location.search);
	// 检测搜索模式
	    const keywordParam = params.get("keyword");
	    if (keywordParam && keywordParam.trim() !== "") {
	        isSearchMode = true;
	        currentKeyword = keywordParam.trim();
	        currentDisplayCategory = null;
	        currentApiCategory = null;
	    } else {
	        // 普通分类模式（与后端参数名一致）
		let displayCat = params.get("article_type");
		if (displayCat && categoryMap[displayCat]) {
			currentDisplayCategory = displayCat;
			currentApiCategory = categoryMap[displayCat];
		} else {
			currentDisplayCategory = "推荐";
			currentApiCategory = categoryMap["推荐"];
		}
	}
    const pageParam = params.get("page");
    if (pageParam) currentPage = parseInt(pageParam);
    else currentPage = 1;
    if (window.startNum === undefined) window.startNum = 0;
    if (window.endNum === undefined) window.endNum = 0;
    if (window.startNum === window.endNum && window.startNum !== 0) {
        document.querySelector(".load-more").innerHTML = "没有更多内容了";
    } else {
        document.querySelector(".load-more").innerHTML = "下滑加载更多内容";
    }
    bindCategoryClicks();
    window.addEventListener("scroll", handleScroll);
    if (location.search.includes("scroll")) {
        window.scrollTo(0, document.body.scrollHeight - 1000);
    }
}

let initialized = false;
document.addEventListener("DOMContentLoaded", () => {
    if (!initialized) {
        init();
        initialized = true;
    }
});