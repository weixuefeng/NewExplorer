'use strict';

//Setting up route
angular.module('insight').config(function($routeProvider) {
  $routeProvider.
    when('/block/:blockHash', {
      templateUrl: 'views/block.html',
      title: 'Block '
    }).
    when('/block-index/:blockHeight', {
      controller: 'BlocksController',
      templateUrl: 'views/redirect.html'
    }).
    when('/tx/send', {
      templateUrl: 'views/transaction_sendraw.html',
      title: 'Broadcast Raw Transaction'
    }).
    when('/tx/:txId/:v_type?/:v_index?', {
      templateUrl: 'views/transaction.html',
      title: 'Transaction '
    }).
    when('/', {
      templateUrl: 'views/index.html',
      title: 'Home'
    }).
    when('/blocks', {
      templateUrl: 'views/block_list.html',
      title: 'Blocks solved Today'
    }).
    when('/blocks-date/:blockDate/:timezone/:startTimestamp?', {
      templateUrl: 'views/block_list.html',
      title: 'Blocks solved '
    }).
    when('/transactions-date/:transDate/:timezone/:startTimestamp?', {
      templateUrl: 'views/transaction_list.html',
      title: 'Transactions list '
    }).
    when('/transactions', {
      templateUrl: 'views/transaction_list.html',
      title: 'Transactions list today'
    }).
    when('/address/:addrStr/:type', {
      templateUrl: 'views/address.html',
      title: 'Address '
    }).
    when('/address/:addrStr', {
      templateUrl: 'views/address.html',
      title: 'Address '
    }).
    when('/status', {
      templateUrl: 'views/status.html',
      title: 'Status'
    }).
    when('/addrs/richest-list', {
      templateUrl: 'views/rank.html',
      title: 'rank'
    }).
    when('/messages/verify', {
      templateUrl: 'views/messages_verify.html',
      title: 'Verify Message'
    }).
    when('/contracts', {
      templateUrl: 'views/contract_list.html',
      title: 'Contracts'
    }).
    when('/contracts/:pageNum', {
      templateUrl: 'views/contract_list.html',
      title: 'Contracts'
    }).
    when('/address', {
    templateUrl: 'views/accounts.html',
    title: 'Accounts '
    }).
    when('/address/:pageNum', {
      templateUrl: 'views/accounts.html',
      title: 'Accounts '
    }).
    when('/contract/:contractAddr', {
      templateUrl: 'views/contract.html',
      title: 'Contract'
    })
    .otherwise({
      templateUrl: 'views/404.html',
      title: 'Error'
    });
});

//Setting HTML5 Location Mode
angular.module('insight')
  .config(function($locationProvider) {
    $locationProvider.html5Mode(true);
    $locationProvider.hashPrefix('!');
  })
  .run(function($rootScope, $route, $location, $routeParams, $anchorScroll, ngProgress, gettextCatalog, amMoment) {
    gettextCatalog.currentLanguage = defaultLanguage;
    amMoment.changeLocale(defaultLanguage);
    $rootScope.$on('$routeChangeStart', function() {
      ngProgress.start();
    });

    $rootScope.$on('$routeChangeSuccess', function() {
      ngProgress.complete();

      //Change page title, based on Route information
      $rootScope.titleDetail = '';
      $rootScope.title = $route.current.title;
      $rootScope.isCollapsed = true;
      $rootScope.currentAddr = null;

      $location.hash($routeParams.scrollTo);
      $anchorScroll();
    });
  });


// angular.module('insight').config(function($interpolateProvider) {
//     $interpolateProvider.startSymbol('[[');
//     $interpolateProvider.endSymbol(']]');
// });