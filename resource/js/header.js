function search_article(){
	var keyword = document.querySelector(".searchbox").value;
	// console.log(keyword);
	location.href="?keyword="+keyword;
}

// 搜索框支持回车触发搜索
document.addEventListener("keydown", function(e){
	if (e.key === "Enter" && e.target && e.target.classList && e.target.classList.contains("searchbox")) {
		search_article();
	}
});

function sendEmailVCode(){
	// 获取邮箱 
	var targetEmail = document.querySelector("#regEmail").value;
	// 获取到发送按钮
	var sendEmailButton = document.querySelector("#sendCodeBtn");
	
	//也可以进行邮箱格式验证
	if(!targetEmail.match(".+@.+\..+")){
		alert("邮箱格式错误");
		document.querySelector("#regEmail").focus();
		return false
	}
	
	// 比对两次密码是否一致
	var firstPassword = document.querySelector("#regPassword").value;
	var secondPassword = document.querySelector("#regConfirmPwd").value;
	if (firstPassword != secondPassword){
		alert("两次输入的密码不一致")
		document.querySelector("#regPassword").focus();
		return false;
	}
	// 发送邮箱验证码
	axios.post("/ecode",{
		email:targetEmail
	}).then((res)=> {
		console.log(res);
		alert("向后端发送验证码成功");
		// 设置倒计时  一般为60秒
		let times = 5;
		countDown(sendEmailButton,times);
	}).catch(err => {
    console.error(err);
    alert("发送失败，请重试");
	});
}

function countDown(sendEmailButton,times){
	sendEmailButton.disabled = true;
	sendEmailButton.innerHTML= times;
	if(times > 0){
		times = times - 1;
		setTimeout(function(){
			countDown(sendEmailButton,times)
		},1000)
	}else{
		// 到了0秒 一切还原
		sendEmailButton.disabled=false;
		sendEmailButton.innerHTML ="发送";
	}
}


// 用户注册实现
function userReg(){
	// 获取邮箱
	var targetEmail = document.querySelector("#regEmail").value;
	
	//也可以进行邮箱格式验证
	if(!targetEmail.match(".+@.+\..+")){
		alert("邮箱格式错误");
		document.querySelector("#regEmail").focus();
		return false
	}
	
	// 比对两次密码是否一致
	var firstPassword = document.querySelector("#regPassword").value;
	var secondPassword = document.querySelector("#regConfirmPwd").value;
	if (firstPassword != secondPassword){
		alert("两次输入的密码不一致")
		document.querySelector("#regPassword").focus();
		return false;
	}
	
	// 开始执行用户注册,获取用户输入的验证码
	var emailVCode = document.querySelector("#emailCode").value;
	
	axios.post("/reg",{
		username:targetEmail,
		password:firstPassword,
		confirm:secondPassword,
		ecode:emailVCode
	}).then((res)=>{
		// res.data就是后端返回json
		// console.log(res.data)
		if (res.data.status==1000){
			alert(res.data.data);
			// 注册成功后要做一个页面跳转，转到首页
			location.href="/"
		}else{
			alert(res.data.data);
		}
	})
	
}


// 登录功能实现
function doLogin(){
	var username = document.querySelector("#username").value;
	var password = document.querySelector("#password").value;
	var loginCode = document.querySelector("#loginCode").value;
	axios.post("/login",{
		username:username,
		password:password,
		vcode:loginCode,
	}).then((res)=>{
		if(res.data.status==1000){
			alert(res.data.data);
			setTimeout("location.reload()",1000);
		}else{
			alert(res.data.data);
		}
		
	})
}

// 创作页面跳转
function toWriteArticlePage(isLogin){
	console.log(isLogin);
	if(isLogin=='None' || isLogin!='true'){
		alert("您好，请登录");
		document.querySelector(".login>span:first-child").click();
	}else{
		window.open("/article/new","_blank")
	}
}

// 退出登录
function doLogout(){
	fetch("/logout",{method:"POST"}).finally(()=>{
		location.href = "/";
	});
}