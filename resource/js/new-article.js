var ue = UE.getEditor('editor', {
				shortcutMenu: false,
				elementPathEnabled : false,
				autoHeightEnabled:false,
				// 初始化编辑器宽度,默认 800
				initialFrameWidth:738,
				// 初始化编辑器高度,默认 800
				initialFrameHeight:800,
				serverUrl:"http://127.0.0.1:5000/feedback",
		        toolbars: [
					[
						"bold",         // 加粗
						"italic",       // 斜体
						"insertimage",         // 多图上传
						"link",                // 超链接
						"insertorderedlist",   // 有序列表
						"insertunorderedlist", // 无序列表
						"blockquote",   // 引用
						"undo",         // 撤销
						"redo",         // 重做
						"emotion",             // 表情
					]
				]
		    });
			
// 投递栏目的显示与隐藏
var isArticleLabelListShow=true;

function showArticleLabelList(){
	var labelList = document.querySelector(".article-label-list");
	var labelValue = document.querySelector(".article-label-value");
	if(isArticleLabelListShow==true){
		labelList.style.display = "block";
		isArticleLabelListShow=false;
		labelValue.style.boxShadow="0 0 0 4px rgb(28 31 33 / 10%)";
	}else{
		labelList.style.display = "none";
		isArticleLabelListShow=true;
		labelValue.style.boxShadow="";
	}
}

// 发表类型的显示与隐藏
var isArticleTypeListShow=true;
function showArticleTypeList(){
	var typeList = document.querySelector(".article-type-list");
	var typeValue = document.querySelector(".article-type-value");
	if(isArticleTypeListShow==true){
		typeList.style.display = "block";
		isArticleTypeListShow=false;
		typeValue.style.boxShadow="0 0 0 4px rgb(28 31 33 / 10%)";
	}else{
		typeList.style.display = "none";
		isArticleTypeListShow=true;
		typeValue.style.boxShadow="";
	}
}

// 草稿箱的显示与隐藏
var isDraftedListShow=true;
function showDraftedList(){
	var draftedList = document.querySelector(".drafted-info");
	if(isDraftedListShow==true){
		draftedList.style.display = "block";
		isDraftedListShow=false;
	}else{
		draftedList.style.display = "none";
		isDraftedListShow=true;
	}
}
// 自动保存草稿，成功后执行回调
function saveDraftAndThen(callback) {
    // 获取标题和内容
    var titleInput = document.querySelector(".article-header input");
    var title = titleInput ? titleInput.value.trim() : '';
    if (!title) {
        alert('请先填写文章标题');
        return;
    }
	// 获取内容
    var content = ue.getContent();
    // 获取标签和分类
    var tagInput = document.querySelector(".article-tag-value input");
    var article_tag = tagInput ? tagInput.value.trim() : '';
    var finalLabelName = label_name || 'recommend';  // label_name 由 selectLabelName 设置

    axios.post("/article/save", {
        title: title,
        article_content: content,
        article_id: -1,
        drafted: 0,   // 存为草稿
        label_name: finalLabelName,
        article_tag: article_tag
    }).then((res) => {
        if (res.data.article_id) {
            articleId = res.data.article_id;
            if (callback) callback();
        } else {
            alert('草稿保存失败：' + (res.data.data || '未知错误'));
        }
    }).catch(err => {
        console.error(err);
        alert('保存草稿失败，请稍后重试');
    });
}


// 创建文章或者文章的草稿箱
// 声明存储文章内容的变量
var articleContent;
var articleTitle;
var articleId=-1;
// 选择投递的栏目
var label_name = ""
var article_type=""
function createAticle(drafted){
	// 获取文章标题
	// articleTitle = document.querySelector(".article-header").value;
	var titleInput = document.querySelector(".article-header input");
	articleTitle = titleInput ? titleInput.value.trim() : '';
	if (!articleTitle) {
	    alert('请填写文章标题');
	    return;
	}
	// 获取文章内容
	articleContent = ue.getContent();
	console.log("drafted =", drafted);
	// 向后端发送请求
	axios.post("/article/save",{
		// 这是草稿存储的逻辑
		title:articleTitle,
		article_content:articleContent,
		article_id:articleId,
		drafted:drafted,
		// 正式发布文章时使用
		label_name:label_name,
		article_type:article_type,
		article_tag:articleTag
	}).then((res)=>{
		articleId = res.data.article_id;
		alert(res.data.data);
		// 如果是文章发布，需跳转文章详情页
		if(drafted==1){
			setTimeout(function(){
				location.href="/detail?article_id="+articleId;
			},1000);
		}
	}).catch(err=>{
		console.error(err);
		alert('操作失败，请重试');
	})
}

// 添加事件监听，上传文章头部图片
// window.onload是页面加载完毕后立即执行。不使用会报addEnevtListener的错误
// 等待 DOM 完全加载
document.addEventListener("DOMContentLoaded", function() {
    // 获取文件输入框元素
    var fileInput = document.getElementById("xfile");
    if (!fileInput) {
        console.error("未找到 #xfile 元素");
        return;
    }

    // 监听文件选择变化
    fileInput.addEventListener("change", function(event) {
        var file = event.target.files[0];
        if (!file) return;

        // 定义上传函数
        function doUpload() {
            var formData = new FormData();
            formData.append("header-image-file", file);
            formData.append("article_id", articleId);
            axios.post("/article/upload/article_header_image", formData)
                .then((res) => {
                    if (res.data.state === "SUCCESS") {
                        var img = document.querySelector("#publishModal .upload-header-image label img");
                        if (img) {
                            img.src = res.data.url;
                            img.style.width = "100px";
                            img.style.height = "100px";
                        } else {
                            console.error("未找到图片显示元素");
                        }
                    } else {
                        alert(res.data.msg || "上传失败");
                    }
                })
                .catch(err => {
                    console.error("上传请求失败", err);
                    alert("上传失败，请稍后重试");
                });
        }

        // 如果 articleId 为 -1，先保存草稿
        if (articleId === -1) {
            saveDraftAndThen(doUpload);
        } else {
            doUpload();
        }
    });

    // 如果有“本地上传”按钮（用于手动触发文件选择），也可以添加快捷方式
    var uploadBtn = document.querySelector(".upload-header-button");
    if (uploadBtn) {
        uploadBtn.addEventListener("click", function() {
            fileInput.click();
        });
    }
});

// 保存草稿并执行回调（确保在全局作用域）
function saveDraftAndThen(callback) {
    var titleInput = document.querySelector(".article-header input");
    var title = titleInput ? titleInput.value.trim() : '';
    if (!title) {
        alert('请先填写文章标题');
        return;
    }
    var content = ue.getContent();
    var tagInput = document.querySelector(".article-tag-value input");
    var article_tag = tagInput ? tagInput.value.trim() : '';
    var finalLabelName = label_name || 'recommend';

    axios.post("/article/save", {
        title: title,
        article_content: content,
        article_id: -1,
        drafted: 0,
        label_name: finalLabelName,
        article_tag: article_tag
    }).then((res) => {
        if (res.data.article_id) {
            articleId = res.data.article_id;
            if (callback) callback();
        } else {
            alert("草稿保存失败：" + (res.data.data || "未知错误"));
        }
    }).catch(err => {
        console.error(err);
        alert("保存草稿失败，请稍后重试");
    });
}

// 文章头像的随机选择
function randomHeaderImage() {
    if (articleId == -1) {
        saveDraftAndThen(function() {
            doRandomHeaderImage();
        });
    } else {
        doRandomHeaderImage();
    }
}

function doRandomHeaderImage() {
	// 构造请求参数
    var formData = new FormData();
    formData.append("article_id", articleId);
	// 把数据提交给后台
    axios.post("/article/random/header/image", formData).then((res) => {
        if (res.data.state === 'SUCCESS') {
            var image = document.querySelector(".upload-header-image label img");
            image.setAttribute("src", res.data.url);
            image.style.width = "100px";
            image.style.height = "100px";
        } else {
            alert(res.data.msg || '随机封面失败');
        }
    }).catch(err => {
        console.error(err);
        alert('网络错误');
    });
}


// 选择投递的栏目
function selectLabelName(label_name_args,label_value_args){
	label_name = label_name_args;
	var firstChildSpan = document.querySelector(".article-label-value>span:first-child");
	firstChildSpan.innerHTML = label_value_args;
	// if (firstChildSpan) firstChildSpan.innerHTML = label_value_args;
	var lis = document.querySelector(".article-label-list>div>li");
	// 这里的for循环，如果使用了in那么就会多遍历出来一些属性，因为in会把lis当成对象来遍历，会把其他属性也循环出来。
	for(var i = 0; i < lis.length; i++){
		// console.log(i);
		lis[i].className = "no-selected";
		if(lis[i].getAttribute("data-label-type") == label_name_args){
			lis[i].className="selected";
		}
	}
}

// 选择文章的类型
function selectArticleType(article_type_name_args,article_type_value_args){
	article_type = article_type_name_args;
	var firstChildSpan = document.querySelector(".article-type-value>span:first-child");
	firstChildSpan.innerHTML = article_type_value_args;
	// if (firstChildSpan) firstChildSpan.innerHTML = type_value_args;
	var lis = document.querySelector(".article-type-list>div>li");
	// 这里的for循环，如果使用了in那么就会多遍历出来一些属性，因为in会把lis当成对象来遍历，会把其他属性也循环出来。
	for(var i = 0; i < lis.length; i++){
		// console.log(i);
		lis[i].className = "no-selected";
		if(lis[i].getAttribute("data-article-type") == article_type_name_args){
			lis[i].className="selected";
		}
	}
}

// 添加文章标签
var articleTag="";  //存储到数据库的样子
var finalTagsList = []; //这个是用来做中间转换用的
var tagNum = 0;
function addTag(tagName){
	if(finalTagsList.length==3){
		return false;
	}
	//我们需要定位到change-tags，给他添加子元素
	var changeTags = document.querySelector(".change-tags")
	var childElement = "span";
	var mySpanTag = document.createElement(childElement);
	//<span>心情</span>
	mySpanTag.innerHTML=tagName;
	mySpanTag.setAttribute("data-tag",tagName);
	mySpanTag.addEventListener("click",deleteTag);
	finalTagsList.push(tagName);
	articleTag = finalTagsList.join(",");
	changeTags.appendChild(mySpanTag);
	//如果标签数量达到三个，删除input标签
	if(finalTagsList.length==3){
		var tagInputElement = document.querySelector(".article-tag-value>input");
		document.querySelector(".article-tag-value").removeChild(tagInputElement);
	}
	// 修改前端标签数量显示
	document.querySelector(".tag-num").innerHTML= finalTagsList.length;
}

function deleteTag(){
	var changeTags = document.querySelector(".change-tags");
	var changeSonTags = document.querySelectorAll(".change-tags>span");
	for(var i of changeSonTags.keys()){
		if(changeSonTags[i].getAttribute("data-tag")==this.innerHTML){
			changeTags.removeChild(changeSonTags[i])
		}
		// 删除完之后，对数组中的元素进行删除，然后再改变最终的字符串
		for(i in finalTagsList){
			if(finalTagsList[i]==this.innerHTML){
				finalTagsList.splice(i,1);
				articleTag=finalTagsList.join(",");
			}
		}
	}
	// 如果长度小于3，判断孩子里面有没有input标签，没有的话添加
	// <input class="fl" type="text" placeholder="选择下列标签"/>
	var tagInputElement = document.querySelector(".article-tag-value>input");
	if(tagInputElement==null){
		var articleTagValue = document.querySelector(".article-tag-value");
		tagInputElement = document.createElement("input");
		tagInputElement.className = "fl";
		tagInputElement.type="text";
		tagInputElement.setAttribute("placeholder","选择下列标签");
		articleTagValue.appendChild(tagInputElement);
		// 手动绑定监听事件
		addInputEventListenerFunc();
	}
	// 修改前端标签的数量
	document.querySelector(".tag-num").innerHTML= finalTagsList.length;
}

// 修复input标签删除后，在重建没有监听事件的bug
var addInputEventListenerFunc;

window.onload=function(){
	function addInputEventListener(){
		var article_tags = window.globalArticleTags;
		console.log(article_tags);
		var inputElement = document.querySelector(".article-tag-value>input");
		inputElement.addEventListener("input",function(event){
			var resetArticleTagList=[];
			var tag_value = inputElement.value;
			console.log(tag_value);
			// 动态渲染，重新筛选标签
			for(var i in article_tags){
				if(article_tags[i].search(tag_value)!=-1){
					resetArticleTagList.push(article_tags[i]);
				}
			}
			// 再次渲染页面
			var articleTagListElement = document.querySelector(".article-tag-list");
			// 先删除掉所有孩子，然后在用新的列表内容进行标签渲染
			articleTagListElement.innerHTML="";
			for(var i in resetArticleTagList){
				var element = document.createElement("span");
				element.setAttribute("onclick","addTag('"+resetArticleTagList[i]+"')");
				element.innerHTML=resetArticleTagList[i];
				articleTagListElement.appendChild(element)
				
			}
		})
	}
	addInputEventListenerFunc = addInputEventListener;
	addInputEventListenerFunc();
}

// 在ue中显示我的草稿内容
function toDrafted(draftedId){
	// 一个是把title的值给放上去
	var articleHeader = document.querySelector(".article-header>input");
	
	// 把article_content的内容放上
	axios.post("/article/drafted",{
		article_id:draftedId
	}).then((res)=>{
		articleHeader.value = res.data.data.title;
		ue.body.innerHTML=res.data.data.article_content;
		// 千万不要忘记编辑的是哪个草稿
		articleId = res.data.data.article_id;
	})
}