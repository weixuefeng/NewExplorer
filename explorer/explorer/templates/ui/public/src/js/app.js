'use strict';
function _setCookie(cname, isoCode) {
  var expires = "";
  var days = 365;
  var name = cname;
  var value = isoCode;
  if (days) {
      var date = new Date();
      date.setTime(date.getTime() + (days*24*60*60*1000));
      expires = "; expires=" + date.toUTCString();
  }
  document.cookie = name + "=" + value + expires + "; path=/";
}
function _getCookie(cname) {
  var name = cname + "=";
  var ca = document.cookie.split(';');
  for(var i=0; i<ca.length; i++) {
   var c = ca[i];
   while (c.charAt(0)==' ') c = c.substring(1);
   if (c.indexOf(name) != -1) return c.substring(name.length, c.length);
  }
  return "";
}
function _getDefaultLanguage(){
  var language = localStorage.getItem('insight-language');
  if(language) return language;
  language = _getCookie('language');
  if(language) return language;
  language = window.navigator.language;
  if(language.includes("zh")){
    language = "zh_CN";
  }
  _setCookie("language",language);
  return language;
}

var defaultLanguage = _getDefaultLanguage();
var defaultCurrency = localStorage.getItem('insight-currency') || 'New';


angular.module('insight',[
  'ngAnimate',
  'ngResource',
  'ngRoute',
  'ngProgress',
  'ui.bootstrap',
  'ui.route',
  'monospaced.qrcode',
  'gettext',
  'angularMoment',
  'insight.system',
  'insight.socket',
  'insight.api',
  'insight.blocks',
  'insight.transactions',
  'insight.address',
  'insight.search',
  'insight.status',
  'insight.rank',
  'insight.connection',
  'insight.currency',
  'insight.messages'
]);

angular.module('insight.system', []);
angular.module('insight.socket', []);
angular.module('insight.api', []);
angular.module('insight.blocks', []);
angular.module('insight.transactions', []);
angular.module('insight.address', []);
angular.module('insight.search', []);
angular.module('insight.status', []);
angular.module('insight.connection', []);
angular.module('insight.currency', []);
angular.module('insight.messages', []);
angular.module('insight.rank', []);
