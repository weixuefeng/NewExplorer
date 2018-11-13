'use strict';

angular.module('insight.blocks').controller('BlocksController',
  function($scope, $rootScope, $routeParams, $location, Global, Block, Blocks, BlockByHeight) {
  $scope.global = Global;
  $scope.loading = false;
  var a = new Date();
  var timezone = a.getTimezoneOffset() / 60;
  $scope.timezone = timezone;
  // if(timezone < 0){
  //   $scope.timezone = 24+timezone;
  // }else{
  //   $scope.timezone = timezone;
  // }
  if ($routeParams.blockHeight) {
    BlockByHeight.get({
      blockHeight: $routeParams.blockHeight
    }, function(hash) {
      $location.path('/block/' + hash.blockHash);
    }, function() {
      $rootScope.flashMessage = 'Bad Request';
      $location.path('/');
    });
  }

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
      $location.path('/blocks-date/' + _formatTimestamp(newValue) + "/" + $scope.timezone);
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
    if ($routeParams.blockDate) {
      $scope.detail = 'On ' + $routeParams.blockDate;
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

    Blocks.get({
      blockDate: $routeParams.blockDate,
      startTimestamp: $routeParams.startTimestamp,
      timezone: $routeParams.timezone
    }, function(res) {
      $scope.loading = false;
      $scope.blocks = res.blocks;
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

  $scope.findOne = function() {
    $scope.loading = true;

    Block.get({
      blockHash: $routeParams.blockHash
    }, function(block) {
      $rootScope.titleDetail = block.height;
      $rootScope.flashMessage = null;
      $scope.loading = false;
      $scope.block = block;
    }, function(e) {
      if (e.status === 400) {
        $rootScope.flashMessage = 'Invalid Transaction ID: ' + $routeParams.txId;
      }
      else if (e.status === 503) {
        $rootScope.flashMessage = 'Backend Error. ' + e.data;
      }
      else {
        $rootScope.flashMessage = 'Block Not Found';
      }
      $location.path('/');
    });
  };

  $scope.params = $routeParams;

  $rootScope.fsn = false;
});
