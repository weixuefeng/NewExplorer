'use strict';

angular.module('insight.rank').controller('RankController',
  function($scope, $routeParams, $location, Global,GetRichList,Address) {
    $scope.global = Global;
    $scope.loading = true;
//     $scope.sync = [
//{
//percentage: 0.4545454545454242,
//balance: 14999999.999999,
//address: "8KNrJAyF4M67HT5tma7ZE4Rx9N9YzaUbtM"
//},
//{
//percentage: 0.15151515151515152,
//balance: 5000000,
//address: "8K9gkit8NPM5bD84wJuE5n7tS9Rdski5uB"
//},
//{
//percentage: 0.10116898069633333,
//balance: 3338576.362979,
//address: "8S7jTjYjqBhJpS9DxaZEbBLfAhvvyGypKx"
//},
//{
//percentage: 0.06111335562130303,
//balance: 2016740.735503,
//address: "8cTn9JAGXfqGgu8kVUaPBJXrhSjoJR9ymG"
//}
//];

    $scope.getRichList = function(){
        GetRichList.get({},
                        function(sync){
                          $scope.loading = false;
                          $scope.sync = sync;
                        },
                        function(e){
                           $scope.loading = false;
                           var err = 'Could not get sync information' + e.toString();
                            $scope.sync = {
                              error: err
                             };
                        }
                        )
    }

    $scope.getAdress = function(adr){
    window.location='/address/' + adr;

    }
  });