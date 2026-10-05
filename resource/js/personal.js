// 保存个人设置
document.getElementById('saveSettingsBtn').addEventListener('click', function(){
    var data = {
        nickname: document.getElementById('setNickname').value.trim(),
        gender: document.getElementById('setGender').value,
        age: document.getElementById('setAge').value || null,
        address: document.getElementById('setAddress').value.trim(),
        bio: document.getElementById('setBio').value.trim()
    };
    axios.post('/personal/update_settings', data).then(function(res){
        if(res.data.code == 200){
            alert('保存成功');
            location.reload();
        } else {
            alert(res.data.msg || '保存失败');
        }
    }).catch(function(){
        alert('网络错误，请重试');
    });
});

// 头像上传
document.getElementById('avatarFile').addEventListener('change', function(){
    var file = this.files[0];
    if(!file) return;
    var formData = new FormData();
    formData.append('file', file);
    axios.post('/personal/upload_avatar', formData, {
        headers: {'Content-Type': 'multipart/form-data'}
    }).then(function(res){
        if(res.data.code == 200){
            document.getElementById('avatarPreview').src = res.data.picture;
            alert('头像更新成功');
        } else {
            alert(res.data.msg || '上传失败');
        }
    }).catch(function(){
        alert('网络错误，请重试');
    });
});

// 退出登录
document.getElementById('logoutBtn').addEventListener('click', function(){
    if(confirm('确定退出登录吗？')){
        fetch('/logout', {method: 'POST'}).finally(function(){
            location.href = '/';
        });
    }
});
