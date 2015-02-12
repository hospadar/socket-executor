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
        }
    }
})
.controller("socketExecutor", function($scope, socket){
    $scope.stream = socket;
    
})
