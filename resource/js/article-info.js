// 文章收藏功能的实现
// function favoriteUpdate(articleId,canceled){
// 	axios.post("/favorite/update_status",{
// 		article_id:articleId,
// 		canceled:canceled
// 	}).then((res)=>{
// 		if(res.data.status==3000){
// 			window.location.reload()
// 		}else{
// 			alert(res.data.data);
// 		}
// 	})
// }

function collectionUpdate(articleId, canceled) {
    // canceled: 0表示要收藏，1表示要取消收藏
    axios.post("/collection/update_status", {
        article_id: articleId,
        canceled: canceled
    }).then((res) => {
        // 判断状态是否为字符串 "3000"
        if (res.data.status == "3000") {
            // 找到按钮元素
            const btn = document.querySelector('.note-right.fr');
            if (btn) {
                if (canceled == 0) {
                    // 收藏操作成功，将按钮变为“已收藏”
                    btn.innerText = '已收藏';
                    btn.setAttribute('onclick', `collectionUpdate(${articleId}, 1)`);
                } else {
                    // 取消收藏成功，将按钮变为“收藏”
                    btn.innerText = '收藏';
                    btn.setAttribute('onclick', `collectionUpdate(${articleId}, 0)`);
                }
            }
        } else {
            // 其他状态码（如 "3001", "3002"）视为失败，显示错误信息
            alert(res.data.data || "操作失败");
        }
    }).catch((err) => {
        console.error(err);
        alert("网络错误，请稍后重试");
    });
}

// 喜欢功能实现
function likeUpdate(articleId, currentStatus) {
    // currentStatus: 0=喜欢, 1=不喜欢
    // 将要设置的新状态（取反）
    let newStatus = currentStatus == 0 ? 1 : 0;

    axios.post("/favorite/update_status", {
        article_id: articleId,
        canceled: newStatus
    }).then(res => {
        if (res.data.status == "5000") {   // 假设后端成功返回 5000
            const icon = document.getElementById('likeIcon');
            const btn = document.getElementById('likeBtn');
            if (newStatus == 0) {  // 变为喜欢状态
                icon.style.color = '#FE2C55';
                btn.setAttribute('onclick', `likeUpdate(${articleId}, 0)`);
            } else {               // 变为不喜欢状态
                icon.style.color = '#5D5F65';
                btn.setAttribute('onclick', `likeUpdate(${articleId}, 1)`);
            }
        } else {
            alert(res.data.data || "操作失败");
        }
    }).catch(err => {
        console.error(err);
        alert("网络错误，请稍后重试");
    });
}

// 发布评论的UE
 var ue = UE.getEditor('feedback-container', {
				shortcutMenu: false,
				elementPathEnabled : false,
				autoHeightEnabled:false,
				// 初始化编辑器宽度,默认 800
				initialFrameWidth:460,
				// 初始化编辑器高度,默认 320
				initialFrameHeight:100,
				serverUrl:"http://127.0.0.1:5000/feedback",
		        toolbars: [
					[
						"bold",         // 加粗
						"italic",       // 斜体
						// "insertimage",         // 多图上传
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
			
// 发布评论
function addFeedback(articleId){
	var feedbackContent = ue.getContent();
	axios.post("/feedback/add",{
		article_id:articleId,
		content:feedbackContent
	}).then((res)=>{
		alert(res.data.data);
		window.location.reload();
	})
}

// 评论的评论区的输入框控制
// 显示评论具体作者的回复输入框是否展示
var ifShowInputWrap = false;
 // 存储当前打开的输入框id，用来控制关闭
var currentWriteAuthorInputId=0;
// 存储当前评论相关信息，用来向后端发起请求，默认值都给0
var baseReplayId = 0;
var replayArticleId = 0;
var feedbackReplayId = 0;


// 显示输入框
function showWriteAuthorInput(inputId,articleId,userId,nickname,replayId){
	baseReplayId = inputId;
	replayArticleId = articleId;
	feedbackReplayId = replayId;
	// 关闭当前已经打开的输入框
	if (currentWriteAuthorInputId != 0){
		hiddenWriteAuthorInput(currentWriteAuthorInputId);
	}
	currentWriteAuthorInputId = inputId;
	var inputWarp = document.getElementById(inputId);
	if (inputWarp) {
	    inputWarp.style.display = "block";
	} else {
	    console.error("Element with id '" + inputId + "' not found");
	}
	
}
// 隐藏输入框
function hiddenWriteAuthorInput(inputId){
	var inputWarp = document.getElementById(inputId);
	if (inputWarp) {
	    inputWarp.style.display = "none";
	} else {
	    console.error("Element with id '" + inputId + "' not found");
	}
}

// 发布评论的回复评论
function writeReplay(){
	var content = document.getElementById(baseReplayId).querySelector("textarea").value;
	axios.post("/feedback/replay",{
		article_id:replayArticleId,
		content:content,
		replay_id:feedbackReplayId,
		base_replay_id:baseReplayId
	}).then((res)=>{
		alert(res.data.data);
		window.location.reload();
	})
}