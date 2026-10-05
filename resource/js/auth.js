// ==================== 全局状态 ====================
let currentUser = null;

// ==================== 辅助函数 ====================
function showMessage(msg, isError = true) {
    alert(msg);
}

// 更新顶部用户显示
function updateUserDisplay() {
    const userIconSpan = document.getElementById('userTrigger');
    const nicknameSpan = document.getElementById('userNicknameSpan');
    if (!userIconSpan) return;

    if (currentUser) {
        const pictureUrl = currentUser.picture && currentUser.picture !== ''
            ? currentUser.picture
            : 'images/头像.png';
        userIconSpan.innerHTML = `<img src="${pictureUrl}" class="user-avatar-mini" style="width:28px;height:28px;border-radius:50%;">`;
        userIconSpan.style.fontSize = '0';
        nicknameSpan.innerText = currentUser.nickname || currentUser.email.split('@')[0];
        nicknameSpan.style.display = 'inline';
    } else {
        userIconSpan.innerHTML = '&#xe604;';
        userIconSpan.style.fontSize = '25px';
        nicknameSpan.innerText = '';
    }
}

// ==================== API 调用封装 ====================
async function apiFetch(url, options = {}) {
    const res = await fetch(url, {
        ...options,
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        }
    });
    return res.json();
}

// 检查登录状态
async function checkLoginStatus() {
    try {
        const data = await apiFetch('/check_login');
        if (data.is_login) {
            currentUser = data.user;
            updateUserDisplay();
        }
    } catch (e) {
        console.error(e);
    }
}

// 刷新验证码图片
function refreshCaptcha() {
    const captchaImg = document.getElementById('captchaImg');
    if (captchaImg) {
        captchaImg.src = '/vcode?' + Date.now();
    }
    const regCaptchaImg = document.getElementById('regCaptchaImg');
    if (regCaptchaImg) {
        regCaptchaImg.src = '/vcode?' + Date.now();
    }
}



// 登录
async function handleLogin(email, password, code) {
    const data = await apiFetch('/login', {
        method: 'POST',
        body: JSON.stringify({ email, password, code })
    });
    if (data.code === 200) {
        currentUser = data.user;
        updateUserDisplay();
        closeModal('loginModal');
        showMessage('登录成功', false);
    } else {
        showMessage(data.msg);
        refreshCaptcha();
    }
}

// 注册
async function handleRegister(email, password, confirm, code,emailCode) {
    const data = await apiFetch('/register', {
        method: 'POST',
        body: JSON.stringify({ email, password, confirm, code,emailCode })
    });
    if (data.code === 200) {
        showMessage('注册成功，请登录', false);
        closeModal('regModal');
        openModal('loginModal');
    } else {
        showMessage(data.msg);
        refreshCaptcha();
    }
}

// 退出登录
async function logout() {
    await apiFetch('/logout', { method: 'POST' });
    currentUser = null;
    updateUserDisplay();
    closeModal(null);
    const panel = document.getElementById('profilePanel');
    if (panel) panel.style.display = 'none';
    showMessage('已退出登录', false);
}

// 保存个人资料
async function saveProfile(nickname, pictureBase64) {
    if (!currentUser) return;
    const data = await apiFetch('/update_profile', {
        method: 'POST',
        body: JSON.stringify({ nickname, picture: pictureBase64 })
    });
    if (data.code === 200) {
        if (nickname) currentUser.nickname = nickname;
        if (pictureBase64) currentUser.picture = pictureBase64;
        updateUserDisplay();
        document.getElementById('profilePanel').style.display = 'none';
        showMessage('保存成功', false);
    } else {
        showMessage(data.msg);
    }
}

// ==================== 模态框控制 ====================
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        if (modalId === 'loginModal' || modalId === 'regModal') {
            refreshCaptcha();
        }
    }
}
function closeModal(modalId) {
    if (modalId) {
        const modal = document.getElementById(modalId);
        if (modal) modal.style.display = 'none';
    } else {
        document.querySelectorAll('.modal-overlay').forEach(m => m.style.display = 'none');
    }
}
window.switchModal = function(closeId, openId) {
    closeModal(closeId);
    openModal(openId);
};

// ==================== 个人面板 ====================
function showProfilePanel() {
    if (!currentUser) {
        openModal('loginModal');
        return;
    }
    const avatarImg = document.getElementById('profileAvatar');
    const nicknameInput = document.getElementById('profileNickname');
    if (avatarImg) avatarImg.src = currentUser.picture || 'images/头像.png';
    if (nicknameInput) nicknameInput.value = currentUser.nickname || '';
    const panel = document.getElementById('profilePanel');
    if (panel) panel.style.display = 'block';
}

// 头像上传预览并保存 base64 到临时变量
let pendingPictureBase64 = null;
document.addEventListener('change', function(e) {
    if (e.target && e.target.id === 'avatarUpload') {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(ev) {
                document.getElementById('profileAvatar').src = ev.target.result;
                pendingPictureBase64 = ev.target.result;
            };
            reader.readAsDataURL(file);
        }
    }
});

// ==================== 事件绑定 ====================
document.addEventListener('DOMContentLoaded', function() {
    // 登录/注册提交由按钮 onclick 的 doLogin()/userReg()（header.js）处理，
    // 这里仅阻止浏览器默认的 GET 表单提交，避免重复发送不匹配的请求
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
        });
    }
    // 注册表单
    const regForm = document.getElementById('regForm');
    if (regForm) {
        regForm.addEventListener('submit', function(e) {
            e.preventDefault();
        });
    }
    // 发送邮箱验证码由 header.js 的 sendEmailVCode()（onclick）处理，不再重复绑定
    // 保存个人资料按钮
    const saveBtn = document.getElementById('saveProfileBtn');
    if (saveBtn) {
        saveBtn.addEventListener('click', function() {
            const newNickname = document.getElementById('profileNickname').value;
            let pictureData = pendingPictureBase64 || null;
            saveProfile(newNickname, pictureData);
            pendingPictureBase64 = null;
        });
    }
    // 退出登录按钮
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            logout();
        });
    }
    // 人头图标点击
    const userTrigger = document.getElementById('userTrigger');
    if (userTrigger) {
        userTrigger.addEventListener('click', function(e) {
            e.stopPropagation();
            showProfilePanel();
        });
    }
    // 点击外部关闭个人面板
    document.addEventListener('click', function(e) {
        const panel = document.getElementById('profilePanel');
        const trigger = document.getElementById('userTrigger');
        if (panel && trigger && !panel.contains(e.target) && !trigger.contains(e.target) && panel.style.display === 'block') {
            panel.style.display = 'none';
        }
    });
    // 初始化检查登录状态
    checkLoginStatus();
});

// 暴露全局函数
window.closeModal = closeModal;
window.openModal = openModal;
window.switchModal = switchModal;
window.showProfilePanel = showProfilePanel;
window.refreshCaptcha = refreshCaptcha;