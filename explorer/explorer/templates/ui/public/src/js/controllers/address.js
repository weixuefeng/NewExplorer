'use strict';

angular.module('insight.address').controller('AddressController',
  function($scope, $rootScope, $routeParams, $location, Global, Address, Accounts, getSocket) {
    $scope.global = Global;

    //var socket = getSocket($scope);
    var addrStr = $routeParams.addrStr;
    /*
    var _startSocket = function() {
      socket.on('bitcoind/addresstxid', function(data) {
        if (data.address === addrStr) {
          $rootScope.$broadcast('tx', data.txid);
          var base = document.querySelector('base');
          var beep = new Audio(base.href + '/sound/transaction.mp3');
          beep.play();
        }
      });
      socket.emit('subscribe', 'bitcoind/addresstxid', [addrStr]);
    };

    var _stopSocket = function () {
      socket.emit('unsubscribe', 'bitcoind/addresstxid', [addrStr]);
    };

    socket.on('connect', function() {
      _startSocket();
    });

    $scope.$on('$destroy', function(){
      _stopSocket();
    });
    */
    $scope.params = $routeParams;
    $scope.input_focus = function(e) {
        e.target.placeholder = '';
    };
    $scope.input_blur = function(e) {
        e.target.placeholder = $scope.current_page + '/' + $scope.total_page;
    };
    $scope.input_enter = function(e) {
        if (e.which === 13) {
            e.target.blur();
            $scope.jump();
        }
    };
    $scope.first = function() {           // jump to the first page
        $scope.page = 1;
        $scope.findAccount();
    };
    $scope.next = function() {            // jump to the next page
        $scope.page = $scope.page + 1;
        $scope.findAccount();
    };
    $scope.prev = function() {            // jump to the prev page
        $scope.page = $scope.page - 1;
        $scope.findAccount();
    };
    $scope.last = function() {            // jump to the last page
        $scope.page = $scope.total_page;
        $scope.findAccount();
    };
    $scope.jump = function() {
        $scope.jump_page = $scope.q;
        $scope.r = /^[1-9]\d*$/;
        $scope.flag = $scope.r.test($scope.jump_page);
        if (($scope.jump_page && !$scope.flag) || !$scope.jump_page || (parseInt($scope.jump_page) === $scope.current_page)) {
            $scope.q = '';
            return;
        }
        $scope.q = '';
        $scope.page = $scope.jump_page;
        $scope.findAccount();
    };
    $scope.findAccount = function() {
        if (!$scope.page) {
            $scope.page = 1;
        }
        Accounts.get({
            pageNum: $scope.page
        },
        function(res) {
            $scope.loading = false;
            $scope.accounts = res.account_list;
            $scope.total_page = res.total_page;
            $scope.current_page = res.current_page;
            $scope.total_addresses = res.total_addresses;
            $scope.total_transactions = res.total_transactions;
        }
       );
    };
    $scope.findOne = function() {
      $rootScope.currentAddr = $routeParams.addrStr;
      //_startSocket();
      Address.get({
          addrStr: $routeParams.addrStr,
          type: $routeParams.type
        },
        function(address) {
          $rootScope.titleDetail = address.addrStr.substring(0, 7) + '...';
          $rootScope.flashMessage = null;
          $scope.is_internal = address.is_internal;
          $scope.has_internal = address.has_internal;
          $scope.address = address;
          $scope.address.totalReceived = scientificToNumber($scope.address.totalReceived,$scope.address.totalReceivedSat)
          $scope.address.totalSent = scientificToNumber($scope.address.totalSent,$scope.address.totalSentSat)
          $scope.address.balance = scientificToNumber($scope.address.balance,$scope.address.balanceSat)
        },
        function(e) {
          if (e.status === 400) {
            $rootScope.flashMessage = 'Invalid Address: ' + $routeParams.addrStr;
          } else if (e.status === 503) {
            $rootScope.flashMessage = 'Backend Error. ' + e.data;
          } else {
            $rootScope.flashMessage = 'Address Not Found';
          }
          $location.path('/');
        });
    };
    function scientificToNumber(value,sat) {
      if(!value){
        return (sat / 1e8).toString();
      }
      var tmp = value.toString()
      if(tmp.includes("e") || tmp.includes("E")){
        var res = tmp.split("e-") || tmp.split("E-");
        var precision = parseInt(res[1]) - 1;
        var zero = "";
        var num = sat.toString()
        for(var i = 0;i < precision;i++){
          zero += "0";
        }
        value = "0." + zero + num;
        return value;
      }
      return value
    }

    $rootScope.fsn = false;
  });
