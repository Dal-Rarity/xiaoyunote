// 点击消息 -> 标记已读并跳转
function readNotification(notificationId, link) {
    axios.post("/message/read", {
        notification_id: notificationId
    }).then(function(res) {
        window.location.href = link;
    }).catch(function(err) {
        window.location.href = link;
    });
}

// 全部标记已读
function markAllRead() {
    axios.post("/message/read_all").then(function(res) {
        if (res.data.status == "8000") {
            window.location.reload();
        } else {
            alert(res.data.data || "操作失败");
        }
    }).catch(function(err) {
        alert("网络错误，请稍后重试");
    });
}

// header 未读消息数量轮询
function pollUnreadCount() {
    fetch("/message/unread_count").then(function(res) {
        return res.json();
    }).then(function(data) {
        if (data.status == "8000") {
            var badge = document.getElementById("messageBadge");
            var count = data.data;
            if (badge) {
                if (count > 0) {
                    badge.innerText = count > 99 ? '99+' : count;
                    badge.style.display = "inline-block";
                } else {
                    badge.style.display = "none";
                }
            }
        }
    }).catch(function(err) {
        // 静默失败
    });
}

// 每30秒轮询一次
if (document.getElementById("messageBadge")) {
    setInterval(pollUnreadCount, 30000);
}
