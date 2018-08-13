'use strict';

var TRANSACTION_DISPLAYED = 10;
var BLOCKS_DISPLAYED = 10;

angular.module('insight.system').controller('IndexController',
  function($scope, Global, getSocket, Blocks, NewTransactions) {
      $scope.global = Global;
      var tradeNumberAnimation = null;
      var _getBlocks = function() {
          Blocks.get({
              limit: BLOCKS_DISPLAYED
          }, function(res) {
              $scope.blocks = res.blocks;
              $scope.blocksLength = res.length;
              var numberOfTransactions = res.number_of_transactions;
              // countup
              if (!tradeNumberAnimation) {
                  tradeNumberAnimation = new CountUp("transaction-number", numberOfTransactions, numberOfTransactions, 0, 10, {separator:' ', useGrouping:false});
                  tradeNumberAnimation.start();
              } else {
                  tradeNumberAnimation.update(numberOfTransactions);
              }
          });
      };
      var _getTransactions = function() {
          NewTransactions.get({
              limit: TRANSACTION_DISPLAYED
          }, function(res) {
              $scope.txs = res.txs
          })
      };

    /*
    var socket = getSocket($scope);

    var _startSocket = function() { 
      socket.emit('subscribe', 'inv');
      socket.on('tx', function(tx) {
        $scope.txs.unshift(tx);
        if (parseInt($scope.txs.length, 10) >= parseInt(TRANSACTION_DISPLAYED, 10)) {
          $scope.txs = $scope.txs.splice(0, TRANSACTION_DISPLAYED);
        }
      });

      socket.on('block', function() {
        _getBlocks();
      });
    };

    socket.on('connect', function() {
      _startSocket();
    });
    */


    $scope.humanSince = function(time) {
      var m = moment.unix(time);
      return m.max().fromNow();
    };

    $scope.index = function() {
        _getBlocks();
        _getTransactions();
        setInterval(function(){
            _getBlocks();
            _getTransactions();
        }, 3 * 1000);
      //_startSocket();
    };

    $scope.txs = [];
    $scope.blocks = [];

    // function createChart(response) {
    //     var data = [];
    //     var values = response.values;
    //     for(var i=0; i<values.length; i++) {
    //         data.push(values[i]["y"]);
    //     }
    //     var d = new Date();
    //     var m = d.getMonth();
    //     var startMonth = d.setMonth( m - 4);
    //     var myChart = Highcharts.chart("price-chart",
    //                                  {
    //                                      chart:{},
    //                                      title:{text:""},
    //                                      credits:{enabled:false},
    //                                      tooltip:{enabled:false},
    //                                      xAxis:{
    //                                          lineColor:"#565459",
    //                                          lineWidth:0.5,
    //                                          categories: ['08-24', '09-01', '10-01', '11-01']
    //                                      },
    //                                      yAxis:{
    //                                          title:"",
    //                                          gridLineColor:"transparent",
    //                                          opposite:true,
    //                                          lineColor:"#565459",
    //                                          lineWidth:0.5
    //                                      },
    //                                      plotOptions:{
    //                                          series:{
    //                                              marker:{
    //                                                  enabled:false,
    //                                                  states:{
    //                                                      hover:{
    //                                                          enabled:false
    //                                                      }
    //                                                  }
    //                                              },
    //                                          }
    //                                      },
    //                                      series:[
    //                                          {
    //                                              name:"Price",
    //                                              data:data,
    //                                              color:"#004a7c",
    //                                              showInLegend:false
    //                                          }
    //                                      ]
    //                                  }
    //                                   );
    // }
    var data = {
        values:[
            {'y': 0.001},
            {'y': 0.001},
            {'y': 0.001},
            {'y': 0.001},
        ]
    };
    //createChart(data);
  });
