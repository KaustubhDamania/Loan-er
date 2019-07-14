var botui = new BotUI('my-botui-app');

var i = 0;

var intents = ['loan','get name', 'amount-1','loan period','email','pan','PAN pic upload', 'Aadhar number', 'Aadhar pic front','Aadhar pic back','Loan approved - yes','Bank details']
var ptr = 0;

var amount;

$(document).ready(function(){
  $(".yes-no, .temp, #cam-hidden, #gallery-hidden, .cam-gallery, .amt-ip, .bank-ip").hide();

  amount = 45000;
  $("#emi")[0].innerHTML = 'EMI: &#8377 ' + calc_emi(amount, 18);
  //trial
  bot_txt('Type \'hey\' to chat with me in English, or \'नमस्ते\' for Hindi');

  $(".human").addClass('animated', 'bounceInUp');

});

//bot messages
function bot_txt(msg){
  botui.message.bot({
    delay: 1100,
    loading: true,
    content: msg
  });
}

function calc_emi(amt, dur){
  interest = dur - 12 + 10;
  return Math.ceil(amt*(1 + interest/100)/dur);
}

function accept_or_deny(){
  $(".yes-no").show();
  $('.send-box').hide();
}

$("#yes").click(function(){
  human_txt('yes');
  $(".yes-no").hide();
  $('.send-box').show();
});

$("#no").click(function(){
  human_txt('no');
  $(".yes-no").hide();
  $('.send-box').show();
});

function cam_or_gallery(){
  $(".cam-gallery").show();
  $('.send-box').hide();
}

function cam_send(){
  fileObj = $('#cam-hidden')[0].files[0];
  const objectURL = window.URL.createObjectURL(fileObj);
  console.log(objectURL);

  $('.cam-gallery').hide();
  $('.send-box').show();
  human_img(objectURL, fileObj.toString());
}

function gallery_send(){
  fileObj = $('#gallery-hidden')[0].files[0];
  const objectURL = window.URL.createObjectURL(fileObj);
  console.log(objectURL);

  $('.cam-gallery').hide();
  $('.send-box').show();
  human_img(objectURL, fileObj);
}

function duration(){
  $(".amt-ip").show();
  $('.send-box').hide();
}

function send_duration(){
  var dur = $("#myRange")[0].value;
  human_txt(dur + ' months');
  $('.amt-ip').hide();
  $('.send-box').show();
}

function get_bank(){
  $(".bank-ip").show();
  $('.send-box').hide();
}

function send_bank(){
  var acc = $("#acc-no")[0].value;
  var ifsc = $("#ifsc")[0].value;
  var name = $("#name")[0].value;
  human_txt('Account No.: ' + acc + '\n' + 'IFSC Code: ' + ifsc + '\n' + 'Account holder\'s name: ' + name);
  $('.bank-ip').hide();
  $('.send-box').show();
}

function get_number(){
    $("#text-ip")[0].type = 'number';
}

function remove_number(){
    $("#text-ip")[0].type = 'text';
}

//function to send msg from text-box
$("#send-button").click(function(){
  var msg = $("#text-ip").val();
  $("#text-ip").val('');

  function pan_check(pan) {
      if((pan).length!=10)
          return false;
      if ('PFCHAT'.indexOf(pan[3]) == -1)
          return false;
      if (!($.isNumeric(pan.substring(5,9))))
          return false;
      return true;
  }

  function ifsc_check(ifsc) {
    if(ifsc.length != 11)
        return false
    else if(ifsc[4]!=0)
        return false;
    else if (!($.isNumeric(ifsc.substring(5,11))))
        return false;
    return true;
  }

  if(ptr==7){
      if(msg.length==12){
          human_txt(msg);
      }
      else{
        human_txt(msg,false);
        bot_txt('Please enter a valid Aadhar');
      }
  }
  else if(ptr==2){
      if(parseInt(msg)<25000 || parseInt(msg)>1500000){
          human_txt(msg,false);
          bot_txt('Sorry, but we only provide loans in the range Rs 25000 to 15 lakhs, please re-enter your amount.');
      }
      else{
          human_txt(msg);
      }
  }
  else if(ptr==5){
      if(!pan_check(msg)){
          human_txt(msg,false);
          bot_txt('Please enter a valid PAN.');
      }
      else{
          human_txt(msg);
      }
  }
  else{
      human_txt(msg);
  }

});

function human_txt(msg, send=true){
  botui.message.human({
    content: msg
  });
  //insert logic to send msg to dialogflow
  if(send)
    send_to_server(msg);

}

function human_img(src, obj){
  botui.message.human({
    type: 'embed',
    content: src
  });
  send_to_server('xyz', true);
}

function send_to_server(msg, is_img=false){
    var url = window.location.href;
    url = url.slice(0,url.length-5)+'/myapi';

    var xhttp = new XMLHttpRequest();

    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            console.log(this.responseText);
            var response = JSON.parse(this.responseText);
            messages = (response.fulfillmentMessages);
            var intent_name = response.intent.displayName;
            console.log(intent_name);
            console.log(messages);
            for (var response in messages) {
                response = messages[response].text.text;
                bot_txt(response[0]);
            }
            if(intent_name != 'Default Fallback Intent'){
                ptr += 1;
                if(ptr<intents.length) {
                    nextIntent = intents[ptr];
                    switch (nextIntent) {
                        case 'email':
                            console.log('25% completed :))');
                            progress();
                            break;
                        case 'amount-1':
                            get_number();
                            break;
                        case 'loan period':
                            remove_number();
                            duration();
                            break;
                        case 'Aadhar number':
                            progress();
                            break;
                        case 'PAN pic upload':
                        case 'Aadhar pic front':
                        case 'Aadhar pic back':
                            cam_or_gallery();
                            break;
                        case 'Loan approved - yes':
                            progress();
                            accept_or_deny();
                            break;
                        case 'Bank details':
                            get_bank();
                            break;
                    }
                }
                else {
                    progress();
                }
            }
        }
    };
    xhttp.open("POST", url, true);
    if(is_img)
        xhttp.setRequestHeader('file_type','image')
    xhttp.send(msg);

    console.log('Some shit');
}

function progress(){
  var elem = $(".progress-bar");
  var width = (elem[0].style.width).toString();
  width = width.substring(0, width.length - 1);   //converting percentage to number
  var steps = 0;
  var id = setInterval(frame, 10);
  console.log(width, steps);
  function frame() {
    if (width >= 100 | steps >= 25)
      clearInterval(id);
    else{
      width++;
      steps++;
      elem[0].style.width = width + '%';
    }
  }
}

function call(){
    location.href = "tel:7021243864";
}

$("#myRange").on('input', function(){
  dur  =this.value;
  let temp = amount;
  $("#emi")[0].innerHTML = 'EMI: &#8377 ' + calc_emi(temp, dur);
  $("#dur")[0].innerHTML = 'Duration: ' + dur + ' months';
});
