'use strict';

angular.module('insight.contracts').controller('ContractsController',
	function($scope, $rootScope, $routeParams, $location, Global, Contracts, Contract) {
    	$scope.global = Global;
    	console.log("enter contracts");
    	var _judgePage = function() {
    		if ($routeParams.pageNum > 1) {
                $scope.pageNum = parseInt($routeParams.pageNum);
            }
            else {
                $scope.pageNum = 1;
            };
    	};

    	$scope.list = function() {
    		Contracts.get({pageNum:$routeParams.pageNum},function(res){
    			$scope.contract_list = res.contract_list;
    			$scope.pagination = parseInt(res.pagination);
    			$scope.is_more = res.is_more;
    			_judgePage();
    		})
    	};

        $scope.findOne = function() {
            Contract.get({contractAddr:$routeParams.contractAddr},function(res){
                $scope.contract = res.contract;
            })
        };
    });