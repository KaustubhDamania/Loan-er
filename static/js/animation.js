function fadeOut(x) {
  $(x).removeClass('fadeIn');
  $(x).addClass('fadeOut');
}

//invalid mob no number
function invalidNo(){
  swal({
    text: 'Please enter a 10 digit number',
    icon: 'error'
  })
}
