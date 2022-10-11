
 let arr_en = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'];
 let arr_EN = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'];
 let arr_symb = ['!', '@', '#', '$', '%', '&', '?', '-', '+', '=', '~'];
 let arr_num = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"];
 let arr_symbName = ['@', '.'];

function checkPasswordMastContain(word) {
    let a = 0, b = 0, c = 0, d = 0;
    for (let i = 0; i < word.length; i++) {
        if (arr_en.indexOf(word[i]) >= 0){
            a++;
        }
        else if (arr_EN.indexOf(word[i]) >= 0) {
            b++
        }
        else if (arr_num.indexOf(word[i]) >= 0 ) {
            d++
        }
        if (a > 0 && b > 0 && d > 0){
            return false;    
        }
    }
    //return true;
    return false;
}

function checkPasswordInvalidSymbol(word) {

    for (let i = 0; i < word.length; i++) {
        if (arr_en.indexOf(word[i]) === -1 && arr_EN.indexOf(word[i]) === -1 
        && arr_symb.indexOf(word[i]) === -1 && arr_num.indexOf(word[i]) === -1) {
            console.log(word[i])
            return true;
        }   
    }
        return false;    
}


 function checkUsernameInvalidSymbol(word) {

    for (let i = 0; i < word.length; i++) {
        if (arr_en.indexOf(word[i]) === -1 && arr_EN.indexOf(word[i]) === -1 
        && arr_symbName.indexOf(word[i]) === -1 && arr_num.indexOf(word[i]) === -1) {
            return true;
        }
    }
    return false;    
}

function checkUsernameMastContain(word) {
   /* for (let i = 0; i < word.length; i++) {
        if (arr_en.indexOf(word[i]) >= 0 || arr_symbName.indexOf(word[i]) >= 0 ){
            return false;  
        }
    }
    return true; */
    return false
}

function show_alert(text) {
    if(confirm(text)) {
        return true;
    }
    return false;
}

function checkCookies(){
    let cookieDate = localStorage.getItem('cookieDate');
    let cookieNotification = document.getElementById('cookie_notification');
    let cookieBtn = cookieNotification.querySelector('.cookie_accept');

    // Если записи про кукисы нет или она просрочена на 1 год, то показываем информацию про кукисы
    if( !cookieDate || (+cookieDate + 31536000000) < Date.now() ){
        cookieNotification.classList.add('show');
    }

    // При клике на кнопку, в локальное хранилище записывается текущая дата в системе UNIX
    cookieBtn.addEventListener('click', function(){
        localStorage.setItem( 'cookieDate', Date.now() );
        cookieNotification.classList.remove('show');
    })
}
checkCookies();