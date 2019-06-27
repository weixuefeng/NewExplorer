'use strict';

angular.module('insight.transactions').controller('transactionsController',
function($scope, $rootScope, $routeParams, $location, Global, Transaction, TransactionsByBlock, TransactionsByAddress,
         TransactionsByContract, Transaction_list) {
  $scope.global = Global;
  $scope.loading = false;
  $scope.loadedBy = null;
  $rootScope.fsn = false;

  var pageNum = 0;
  var pagesTotal = 1;
  var COIN = 100000000;

  var _aggregateItems = function(items) {
    if (!items) return [];
    var l = items.length;

    var ret = [];
    var tmp = {};
    var u = 0;

    for(var i=0; i < l; i++) {

      var notAddr = false;
      // non standard input
      if (items[i].scriptSig && !items[i].addr) {
        items[i].addr = 'Unparsed address [' + u++ + ']';
        items[i].notAddr = true;
        notAddr = true;
      }

      // non standard output
      if (items[i].scriptPubKey && !items[i].scriptPubKey.addresses) {
        items[i].scriptPubKey.addresses = ['Unparsed address [' + u++ + ']'];
        items[i].notAddr = true;
        notAddr = true;
      }

      // multiple addr at output
      if (items[i].scriptPubKey && items[i].scriptPubKey.addresses.length > 1) {
        items[i].addr = items[i].scriptPubKey.addresses.join(',');
        ret.push(items[i]);
        continue;
      }

      var addr = items[i].addr || (items[i].scriptPubKey && items[i].scriptPubKey.addresses[0]);

      if (!tmp[addr]) {
        tmp[addr] = {};
        tmp[addr].valueSat = 0;
        tmp[addr].count = 0;
        tmp[addr].addr = addr;
        tmp[addr].items = [];
      }
      tmp[addr].isSpent = items[i].spentTxId;

      tmp[addr].doubleSpentTxID = tmp[addr].doubleSpentTxID   || items[i].doubleSpentTxID;
      tmp[addr].doubleSpentIndex = tmp[addr].doubleSpentIndex || items[i].doubleSpentIndex;
      tmp[addr].dbError = tmp[addr].dbError || items[i].dbError;
      tmp[addr].valueSat += Math.round(items[i].value * COIN);
      tmp[addr].value += parseFloat(items[i].value)
      tmp[addr].items.push(items[i]);
      tmp[addr].notAddr = notAddr;
      if (items[i].unconfirmedInput)
        tmp[addr].unconfirmedInput = true;

      tmp[addr].count++;
    }
    angular.forEach(tmp, function(v) {
      v.value = v.value || parseInt(v.valueSat) / COIN;
      v.value = scientificToNumber(v)
      ret.push(v);
    });
    return ret;
  };
  function scientificToNumber(v) {
    if(!v.value){
      return;
    }
    var tmp = v.value.toString()
    if(tmp.includes("e") || tmp.includes("E")){
      var res = tmp.split("e-") || tmp.split("E-");
      var precision = parseInt(res[1]) - 1;
      var zero = "";
      var num = v.valueSat.toString();
      for(var i = 0;i < precision;i++){
        zero += "0";
      }
      v.value = "0." + zero + num;
      return v.value;
    }
    return v.value
  }
  var _processTX = function(tx) {
    // tx.vinSimple = _aggregateItems(tx.vin);
    // tx.voutSimple = _aggregateItems(tx.vout);
    // for(var i = 0;i < tx.vin.length;i++){
    //   tx.vin[i].value = scientificToNumber(tx.vin[i]);
    // }
    // for(var j = 0;j < tx.vout.length;j++){
    //   tx.vout[j].value = scientificToNumber(tx.vout[j]);
    // }
  };

  var _paginate = function(data) {
    $scope.loading = false;

    pagesTotal = data.pagesTotal;
    pageNum += 1;

    data.txs.forEach(function(tx) {
      _processTX(tx);
      $scope.txs.push(tx);
    });
  };

  var _byBlock = function() {
    TransactionsByBlock.get({
      block: $routeParams.blockHash,
      pageNum: pageNum
    }, function(data) {
      _paginate(data);
    });
  };

  var _byAddress = function () {
    TransactionsByAddress.get({
      address: $routeParams.addrStr,
      type: $routeParams.type,
      pageNum: pageNum
    }, function(data) {
      _paginate(data);
    });
  };

  var _byContract = function() {
    TransactionsByContract.get({
      contract: $routeParams.contractAddr,
      pageNum: pageNum
    }, function(data) {
      _paginate(data);
    });
  };

  var _findTx = function(txid) {
    Transaction.get({
      txId: txid,
    }, function(tx) {
      $rootScope.titleDetail = tx.txid.substring(0,7) + '...';
      $rootScope.flashMessage = null;
      $scope.tx = tx;
      _processTX(tx);
      $scope.txs.unshift(tx);
    }, function(e) {
      if (e.status === 400) {
        $rootScope.flashMessage = 'Invalid Transaction ID: ' + $routeParams.txId;
      }
      else if (e.status === 503) {
        $rootScope.flashMessage = 'Backend Error. ' + e.data;
      }
      else {
        $rootScope.flashMessage = 'Transaction Not Found';
      }

      $location.path('/');
    });
  };

  $scope.findThis = function() {
    _findTx($routeParams.txId);
  };

  //Initial load
  $scope.load = function(from) {
    $scope.loadedBy = from;
    $scope.loadMore();
  };

  //Load more transactions for pagination
  $scope.loadMore = function() {
    if (pageNum < pagesTotal && !$scope.loading) {
      $scope.loading = true;

      if ($scope.loadedBy === 'address') {
        _byAddress();
      }
      else if ($scope.loadedBy === 'contract') {
        _byContract();
      }
      else {
        _byBlock();
      }
    }
  };

  // Highlighted txout
  if ($routeParams.v_type == '>' || $routeParams.v_type == '<') {
    $scope.from_vin = $routeParams.v_type == '<' ? true : false;
    $scope.from_vout = $routeParams.v_type == '>' ? true : false;
    $scope.v_index = parseInt($routeParams.v_index);
    $scope.itemsExpanded = true;
  }
  
  //Init without txs
  $scope.txs = [];

  $scope.$on('tx', function(event, txid) {
    _findTx(txid);
  });

  var a = new Date();
  $scope.timezone = a.getTimezoneOffset() / 60;
  // if(timezone < 0){
  //   $scope.timezone = 24+timezone;
  // }else{
  //   $scope.timezone = timezone;
  // }

  //Datepicker
  var _formatTimestamp = function (date) {
    var yyyy = date.getFullYear().toString();
    var mm = (date.getMonth() + 1).toString(); // getMonth() is zero-based
    var dd  = date.getDate().toString();
    var res =  yyyy + '-' + (mm[1] ? mm : '0' + mm[0]) + '-' + (dd[1] ? dd : '0' + dd[0]); //padding
    return res;
  };

  $scope.$watch('dt', function(newValue, oldValue) {
    if (newValue !== oldValue) {
      $location.path('/transactions-date/' + _formatTimestamp(newValue) + "/" + $scope.timezone);
    }
  });

  $scope.openCalendar = function($event) {
    $event.preventDefault();
    $event.stopPropagation();

    $scope.opened = true;
  };

  $scope.humanSince = function(time) {
    var m = moment.unix(time).startOf('day');
    var b = moment().startOf('day');
    return m.max().from(b);
  };

  $scope.list = function() {
    $scope.loading = true;
    $scope.is_today = true;
    if ($routeParams.transDate) {
      $scope.detail = 'On ' + $routeParams.transDate;
    }

    if ($routeParams.startTimestamp) {
      var d=new Date($routeParams.startTimestamp*1000);
      var m=d.getMinutes();
      if (m<10) m = '0' + m;
      $scope.before = ' before ' + d.getHours() + ':' + m;
    }
    if($routeParams.timezone){
      $scope.timezone = $routeParams.timezone;
      }

    $rootScope.titleDetail = $scope.detail;
    Transaction_list.get({
      transDate: $routeParams.transDate,
      startTimestamp: $routeParams.startTimestamp,
      timezone: $routeParams.timezone
    }, function(res) {
      $scope.loading = false;
      $scope.trans = res.trans;
      $scope.pagination = res.pagination;
      var ts = $scope.pagination.currentTs;
      $scope.pagination.currentDate = transferUTC2Locale(ts);
      $scope.pagination.prevDate = transferUTC2Locale(ts - 24 * 60 * 60);
      $scope.pagination.nextDate = transferUTC2Locale(ts + 24 * 60 * 60);
    });
  };

  function transferUTC2Locale(timastamp){
    var a = new Date(timastamp * 1000)
    return a.toLocaleDateString().replace("\/","-").replace("\/","-");
  }
});

angular.module('insight.transactions').controller('SendRawTransactionController',
  function($scope, $http, Api) {
  $scope.transaction = '';
  $scope.status = 'ready';  // ready|loading|sent|error
  $scope.txid = '';
  $scope.error = null;

  $scope.formValid = function() {
    return !!$scope.transaction;
  };
  $scope.send = function() {
    var postData = {
      rawtx: $scope.transaction
    };
    $scope.status = 'loading';
    $http.post(Api.apiPrefix + '/tx/send', postData)
      .success(function(data, status, headers, config) {
        if(typeof(data.txid) != 'string') {
          // API returned 200 but the format is not known
          $scope.status = 'error';
          $scope.error = 'The transaction was sent but no transaction id was got back';
          return;
        }

        $scope.status = 'sent';
        $scope.txid = data.txid;
      })
      .error(function(data, status, headers, config) {
        $scope.status = 'error';
        if(data) {
          $scope.error = data;
        } else {
          $scope.error = "No error message given (connection error?)"
        }
      });
  };
});
