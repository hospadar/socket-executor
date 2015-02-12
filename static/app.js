angular.module("socketExecutor", [
    "ui.bootstrap",
    "ngWebSocket"])
.factory("socket", function($websocket){
    var stream = $websocket("ws://" + location.host + "/websocket");
    
    var messages = [];
    
    stream.onMessage(function(message){
        var parsed = angular.fromJson(message);
        messages.push(parsed);
    })
    
    var methods = {
        messages: messages,
        readyState: function(){
            return stream.readyState;    
        },
        send: function(message){
            stream.send(angular.toJson(message))
        },
        reconnect: function(){
            stream.close(true)
            stream = $websocket("ws://" + location.host + "/websocket");
        }
        
    };
    
    return methods;
})
.controller("socketExecutor", function($scope, socket, $interval){
    $scope.stream = socket;
    $scope.socketState = $scope.stream.readyState();
    $scope.messages = $scope.stream.messages;
    
    //Check socket status every 500ms, if it's not open or changing state, try to reconnect
    $interval(function(){
        $scope.socketState = $scope.stream.readyState();
        if ($scope.socketState == 3 || $scope.socketState == 4){
            $scope.stream.reconnect();
        }
    },
    500);
})
