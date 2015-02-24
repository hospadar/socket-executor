angular.module("socketExecutor", [
    "ui.bootstrap",
    "ngWebSocket",
    "luegg.directives"])
.filter('unique', function () {

  return function (items, filterOn) {

    if (filterOn === false) {
      return items;
    }

    if ((filterOn || angular.isUndefined(filterOn)) && angular.isArray(items)) {
      var hashCheck = {}, newItems = [];

      var extractValueToCompare = function (item) {
        if (angular.isObject(item) && angular.isString(filterOn)) {
          return item[filterOn];
        } else {
          return item;
        }
      };

      angular.forEach(items, function (item) {
        var valueToCheck, isDuplicate = false;

        for (var i = 0; i < newItems.length; i++) {
          if (angular.equals(extractValueToCompare(newItems[i]), extractValueToCompare(item))) {
            isDuplicate = true;
            break;
          }
        }
        if (!isDuplicate) {
          newItems.push(item);
        }

      });
      items = newItems;
    }
    return items;
  };
})
.factory("socket", function($websocket){
    var stream = undefined
    
    var logs = [];
    var messages = [];
    var running = false;
    
    //set up the socket
    function init(){
        stream = $websocket("ws://" + location.host + "/websocket");
        stream.onMessage(function(message){
            var parsed = angular.fromJson(message.data);
            if (parsed['type'] == 'output'){
                logs.push(parsed);
                if (logs.length > 500){
                    logs.shift();
                }
            } else {
                if (parsed["type"] == "status"){
                    running=parsed["running"];
                }
                messages.push(parsed);
                if (messages.length > 100){
                    messages.shift();
                }
            }
        })
        stream.send({
            directive: "status"
        });
    }
    
    init();
    
    var methods = {
        messages: messages,
        logs: logs,
        running: function(){
            return running
        },
        readyState: function(){
            return stream.readyState;    
        },
        send: function(message){
            stream.send(angular.toJson(message))
        },
        reconnect: function(){
            stream.close(true)
            init()
        },
        history: function(){
            stream.send(angular.toJson({directive:"history"}));
        }
        
    };
    
    return methods;
})
.controller("socketExecutor", function($scope, socket, $interval, $timeout){
    $scope.stream = socket;
    $scope.stream.history();
    $scope.socketState = $scope.stream.readyState();
    $scope.messages = $scope.stream.messages;
    $scope.logs = $scope.stream.logs;
    
    $scope.roundOne = false;
    $scope.roundTwo = false;
    $scope.roundThree = false;
    
    
    //Check socket status every 500ms, if it's not open or changing state, try to reconnect
    $interval(function(){
        $scope.socketState = $scope.stream.readyState();
        //$scope.running = $scope.running()
        if ($scope.socketState == 3 || $scope.socketState == 4){
            $scope.stream.reconnect();
        }
    },
    500);
    
    $interval(function(){
        $scope.stream.send({
            directive: "status"
        });
    }, 5000)
    
    $scope.interrupt = function(){
        
        $scope.stream.send({
            directive: "interrupt"
        });
        $scope.roundOne = false;
        $scope.roundTwo = false;
        
    }
    
    $scope.terminate = function(){
        
        $scope.stream.send({
            directive: "kill"
        });
        $scope.roundOne = false;
        $scope.roundTwo = false;
        
    }
})
