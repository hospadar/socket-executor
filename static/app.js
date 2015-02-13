angular.module("socketExecutor", [
    "ui.bootstrap",
    "ngWebSocket",
    "luegg.directives"])
.factory("socket", function($websocket){
    var stream = $websocket("ws://" + location.host + "/websocket");
    
    var logs = [];
    var messages = [];
    var messageNum = 0;
    var logNum = 0;
    
    
    stream.onMessage(function(message){
        var parsed = angular.fromJson(message.data);
        if (parsed['type'] == 'output'){
            parsed["index"] = logNum;
            logNum += 1;
            logs.push(parsed);
            if (logs.length > 1000){
                logs.shift();
            }
        } else {
            parsed['index']=messageNum;
            messageNum += 1;
            messages.push(parsed);
            if (messages.length > 1000){
                messages.shift();
            }
        }
    })
    
    var methods = {
        messages: messages,
        logs: logs,
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
    $scope.logs = $scope.stream.logs;
    
    $scope.directives = ["status", "terminate", "poke"];
    $scope.selectedDirective="status";
    $scope.command = "";
    
    //Check socket status every 500ms, if it's not open or changing state, try to reconnect
    $interval(function(){
        $scope.socketState = $scope.stream.readyState();
        if ($scope.socketState == 3 || $scope.socketState == 4){
            $scope.stream.reconnect();
        }
    },
    500);
    
    $scope.sendCommand = function(){
        
        $scope.stream.send({
            directive: $scope.selectedDirective,
            command: $scope.command.match(/\w+|"(?:\\"|[^"])+"/g)
        });
        
    }
})
