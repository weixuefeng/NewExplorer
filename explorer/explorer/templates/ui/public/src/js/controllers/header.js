'use strict';

angular.module('insight.system').controller('HeaderController',
    function($scope, $rootScope, $modal, getSocket, Global, Block, NewBlock) {
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
    var _getNewBlock = function() {
        NewBlock.get({}, function(res) {
            if (res) {
                // _getBlock(res.hash.toString());
                $scope.totalBlocks = res.height;
            }
        });
    };
    setInterval(_getNewBlock, 20 * 1000);
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
    $rootScope.isCollapsed = true;
  });
