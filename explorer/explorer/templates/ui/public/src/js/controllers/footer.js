'use strict';

angular.module('insight.system').controller('FooterController',
  function($scope, $route, $templateCache, gettextCatalog, amMoment,  Version) {
    $scope.defaultLanguage = defaultLanguage;
    var _getVersion = function() {
      Version.get({},
        function(res) {
          $scope.version = res.version;
        });
    };

    $scope.version = _getVersion();

    $scope.availableLanguages = [{
        name: 'Deutsch',
        isoCode: 'de_DE',
    }, {
        name: 'English',
        isoCode: 'en',
    }, {
        name: 'Spanish',
        isoCode: 'es',
    }, {
        name: 'Japanese',
        isoCode: 'ja',
    }, {
        name: '简体中文',
        isoCode: 'zh_CN',
    }];

    // $scope.setLanguage = function(isoCode) {
    //   gettextCatalog.currentLanguage = $scope.defaultLanguage = defaultLanguage = isoCode;
    //   amMoment.changeLocale(isoCode);
    //   localStorage.setItem('insight-language', isoCode);
    //   var expires = "";
    //   var days = 365;
    //   var name = 'language';
    //   var value = isoCode;
    //   if (days) {
    //       var date = new Date();
    //       date.setTime(date.getTime() + (days*24*60*60*1000));
    //       expires = "; expires=" + date.toUTCString();
    //   }
    //   document.cookie = name + "=" + value + expires + "; path=/";
    //   location.reload();
      //var currentPageTemplate = $route.current.templateUrl;
      //$templateCache.remove(currentPageTemplate);
      //$route.reload();
    // };

  });
