'use strict';


angular.module('insight.system').controller('HeaderController',
    function($scope, $rootScope, $modal, getSocket, gettextCatalog, amMoment, Global, Block) {
    $scope.global = Global;

    $rootScope.currency = {
      factor: 1,
      bitstamp: 0,
      symbol: 'New'
    };

    $scope.menu = [
    {
      'title': 'Blocks',
      'link': 'blocks'
    },{
      'title': 'Transactions',
      'link': 'transactions'
    },{
      'title': 'Address',
      'link': 'address'
    },{
      'title': 'Contracts',
      'link': 'contracts'
    },{
      'title': 'Status',
      'link': 'status'
    }];

    $scope.openScannerModal = function() {
      var modalInstance = $modal.open({
        templateUrl: 'scannerModal.html',
        controller: 'ScannerController'
      });
    };

    // var _getBlock = function(hash) {
    //   Block.get({
    //     blockHash: hash
    //   }, function(res) {
    //     $scope.totalBlocks = res.height;
    //   });
    // };
    // var _getNewBlock = function() {
    //     NewBlock.get({}, function(res) {
    //         if (res) {
    //             $scope.totalBlocks = res.height;
    //         }
    //     });
    // };
    // setInterval(_getNewBlock, 20 * 1000);
    /*
    var socket = getSocket($scope);
    socket.on('connect', function() {
      socket.emit('subscribe', 'inv');

      socket.on('block', function(block) {
        var blockHash = block.toString();
        _getBlock(blockHash);
      });
    });
    */
    $scope.setLanguage = function(isoCode) {
      gettextCatalog.currentLanguage = $scope.defaultLanguage = defaultLanguage = isoCode;
      amMoment.changeLocale(isoCode);
      localStorage.setItem('insight-language', isoCode);
      var expires = "";
      var days = 365;
      var name = 'language';
      var value = isoCode;
      if (days) {
          var date = new Date();
          date.setTime(date.getTime() + (days*24*60*60*1000));
          expires = "; expires=" + date.toUTCString();
      }
      document.cookie = name + "=" + value + expires + "; path=/";
      location.reload();
    };

    function readCookie (name)
    {
        var cookieValue = "";
        var search = name + "=";
        if (document.cookie.length > 0)
        {
            offset = document.cookie.indexOf (search);
            if (offset != -1)
            {
                offset += search.length;
                end = document.cookie.indexOf (";", offset);
                if (end == -1)
                    end = document.cookie.length;
                cookieValue = unescape (document.cookie.substring (offset, end))
            }
        }
        else{
          cookieValue = navigator.language;
          if (cookieValue == 'zh-CN'){
            return 'zh_CN';
          }
          else{
            return cookieValue;
          };
        }
        return cookieValue;
    };
    
    $scope.dateValue = readCookie('language');
    $scope.changeLanguage = function(language_code){
              $scope.setLanguage(language_code);
            };

    $rootScope.isCollapsed = true;

    $scope.$on('$viewContentLoaded', function() {
            alert('1');
    });
  });
