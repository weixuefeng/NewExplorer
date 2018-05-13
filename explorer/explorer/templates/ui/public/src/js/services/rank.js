'use strict';

angular.module('insight.rank')
  .factory('GetRichList',
    function($resource, Api) {
      return $resource(Api.apiPrefix + '/addrs/richest-list');
    });