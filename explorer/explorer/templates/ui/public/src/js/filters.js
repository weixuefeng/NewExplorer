'use strict';

angular.module('insight')
  .filter('startFrom', function() {
    return function(input, start) {
      start = +start; //parse to int
      if(input != null && input != undefined){
        return input.slice(start);
      }
      return input;
    }
  })
  .filter('split', function() {
    return function(input, delimiter) {
      var delimiter = delimiter || ',';
      if(!input){
        return;
      }
      return input.split(delimiter);
    }
  });
