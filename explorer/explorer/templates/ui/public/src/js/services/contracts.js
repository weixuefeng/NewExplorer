'use strict';

angular.module('insight.contracts')
	.factory('Contracts',
		function($resource, Api){
			return $resource(Api.apiPrefix + '/contracts_list');
		})
	.factory('Contract',
		function($resource, Api){
			return $resource(Api.apiPrefix + '/contract/:contractAddr', {
				contractAddr:'@contractAddr'
			}, {
	        get: {
	        method: 'GET',
	        interceptor: {
	          response: function (res) {
	            return res.data;
	          },
	          responseError: function (res) {
	            if (res.status === 404) {
	              return res;
	            }
	          }
	        }
	      }
    	})
		});