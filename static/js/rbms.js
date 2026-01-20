$(document).ready(function(){

    if($("#allTime").is(":checked")){      
        $("#fromTimeLab").attr("hidden", true);
        $("#toTimeLab").attr("hidden", true);
        $("#fromTime").attr("hidden", true);
        $("#toTime").attr("hidden", true);
        $("#fromTime").attr("required", false);
        $("#toTime").attr("required", false);
    }
    else if($("#specTime").is(":checked")){        
        $("#fromTimeLab").attr("hidden", false);
        $("#toTimeLab").attr("hidden", false);
        $("#fromTime").attr("show", true);
        $("#toTime").attr("show", true);
        $("#fromTime").attr("required", true);
        $("#toTime").attr("required", true);
    }

    $("#allTime").click(function(){
        $("#fromTimeLab").attr("hidden", true);
        $("#toTimeLab").attr("hidden", true);
        $("#fromTime").attr("hidden", true);
        $("#toTime").attr("hidden", true);
        $("#fromTime").attr("required", false);
        $("#toTime").attr("required", false);
        

    });

    $("#specTime").click(function(){
        $("#fromTimeLab").attr("hidden", false);
        $("#toTimeLab").attr("hidden", false);
        $("#fromTime").attr("hidden", false);
        $("#fromTime").attr("hidden", false);
        $("#toTime").attr("hidden", false);
        $("#fromTime").attr("required", true);
        $("#toTime").attr("required", true);
    });

});