(function() {
    var hidetooltips = function() {
        $(".nt-tooltip").hide();
    };
    $("#nt-compact").height($(document).height());
    $("#nt-compact").mouseout(function () {
        var checkatr = $("#nt-compact").attr("dont-float");
        
        if (typeof checkatr === typeof undefined || checkatr === false){
            $(this).css({ "background-color": "#222", "margin-left": "-55px"});
        }
    });
    $("#nt-compact").mouseover(function (){
       $(this).css({
           "background-color": "#002E5D",
           "margin-left": "0px"
       });
    });
    
    $("#nt-compact>ul>li>a").mouseover (
    function (){
        // do something!
        hidetooltips();
        liheight = $("#nt-compact>ul>li").outerHeight();
        liwidth = $("#nt-compact>ul>li>a").outerWidth()+8;
        $(this).find(".nt-tooltip").show();
        $(".nt-tooltip").css({
           "z-index": "1000"
        });
    }).mouseout(function() {
        hidetooltips();
    });
    
    hidetooltips();
})();