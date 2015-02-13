angular.module("socketExecutor", [
    "ui.bootstrap",
    "ngWebSocket",
    "luegg.directives"])
.factory("socket", function($websocket){
    var stream = undefined
    
    var logs = [];
    var messages = [];
    var messageNum = 0;
    var logNum = 0;
    var running = false;
    function init(){
        stream = $websocket("ws://" + location.host + "/websocket");
        stream.onMessage(function(message){
            var parsed = angular.fromJson(message.data);
            if (parsed['type'] == 'output'){
                parsed["index"] = logNum;
                logNum += 1;
                logs.push(parsed);
                if (logs.length > 500){
                    logs.shift();
                }
            } else {
                if (parsed["type"] == "status"){
                    running=parsed["running"];
                }
                parsed['index']=messageNum;
                messageNum += 1;
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
        }
        
    };
    
    return methods;
})
.controller("socketExecutor", function($scope, socket, $interval, $timeout){
    $scope.stream = socket;
    $scope.socketState = $scope.stream.readyState();
    $scope.messages = $scope.stream.messages;
    $scope.logs = $scope.stream.logs;
    //$scope.running = $scope.stream.running;
    
    $scope.directives = ["status", "terminate"];
    $scope.selectedDirective="status";
    $scope.command = "";
    
    $scope.roundOne = false;
    $scope.roundTwo = false;
    
    
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
    
    $scope.terminate = function(){
        
        $scope.stream.send({
            directive: "terminate"
        });
        $scope.roundOne = false;
        $scope.roundTwo = false;
        
    }
})
