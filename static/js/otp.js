//to go to next digit's box automatically
$(".otp-digit").keyup(function () {
    // console.log('hey')
    if (this.value.length == this.maxLength) {
      $(this).next('.otp-digit').focus();
    }
});

//to go to previous digit's box automatically
$('.otp-digit').keyup(function(e){
  if(e.keyCode == 8 || e.keyCode == 67)  //8 for desktop keyboard's backspace and 67 for android keyboard
    $(this).prev('.otp-digit').focus();
  }
);

//to resend otp
function resendOtp(){
  swal({
    text: 'OTP sent',
    icon: 'success'
  }).then(
    () => {window.location.href='/resend-otp';
  });
}
