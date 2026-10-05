// 关注/取消关注切换
function toggleFollow(userId) {
    var btn = event.currentTarget || event.target;
    var isFollowed = btn.classList.contains('followed');
    var canceled = isFollowed ? 1 : 0;

    axios.post("/follow/update_status", {
        following_id: userId,
        canceled: canceled
    }).then(function(res) {
        if (res.data.status == "7000") {
            if (canceled == 0) {
                btn.classList.add('followed');
                btn.innerText = '已关注';
            } else {
                btn.classList.remove('followed');
                btn.innerText = '+ 关注';
            }
        } else {
            alert(res.data.data || "操作失败");
        }
    }).catch(function(err) {
        console.error(err);
        alert("网络错误，请稍后重试");
    });
}
