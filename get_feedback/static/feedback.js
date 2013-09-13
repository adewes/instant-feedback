
var feature_types = ['vote','input','rate','scale','check','select'];
var survey_key = null;
var session_key = null;
var show_summary = getParameterByName('show_summary');
var survey_server_url = '';

function getParameterByName(name) {
    name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
        results = regex.exec(location.search);
    return results == null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
}

function initialize_feature(feature_type,feature_id,value,admin)
{
    if (feature_type == 'input' || feature_type == 'rate' || feature_type == 'select')
    {
        $(function(){
        $('[rel=popover]').popover({ 
        html : true, 
        placement: 'bottom',
        content: function() {
        return $('#popover_content_wrapper').html();
        }
        });
        });
    }
    else if (feature_type == 'check')
    {
    }
    else if (feature_type == 'scale')
    {
        if (admin)
        {
            init_slider_value(feature_id,value['average']);
        }
        else
        {
            init_slider_value(feature_id,value);
            function build_move_callback(feature_id) {
                return function(event) {
                    return move_slider_value(event,feature_id);
                }            
            };

            function build_click_callback(feature_id) {
                return function(event) {
                    return update_slider_value(event,feature_id);
                }            
            };

            function build_mouseout_callback(feature_id) {
                return function(event) {
                    return init_slider_value(feature_id,value);
                }            
            };

            $('#'+feature_type+'_'+feature_id+'_gradient').mousemove(build_move_callback(feature_id));
            $('#'+feature_type+'_'+feature_id+'_gradient').mouseout(build_mouseout_callback(feature_id));
            $('#'+feature_type+'_'+feature_id+'_gradient').click(build_click_callback(feature_id));
        }
    }
}

function initialize_elements()
{
    if (! survey_key)
    {
        return;
    }
    for(var i=0;i<feature_types.length;i++)
    {
        feature_type = feature_types[i];
        elements = document.getElementsByClassName('survey_'+feature_type);
        for(var j=0;j<elements.length;j++)
        {
            element = elements[j];
            feature_id = element.id;

            function build_callback(element,feature_type,feature_id) {
                    return function(data) {
                    if (data['status'] = 200)
                    {
                        var new_element = element;
                        new_element.innerHTML = data['html'];
                        element.parentNode.replaceChild(element,new_element);
                        initialize_feature(feature_type,feature_id,data['value'],data['admin']);
                    }
                }            
            };
            var jqxhr = $.ajax({
            url:survey_server_url+(show_summary ? '/show_summary/' : '/get_html/')+survey_key+'/'+feature_type+'/'+feature_id+(session_key ? '?session_key='+session_key: ''),
            data:{},
	    cache: false,
            type:'GET',
            dataType:'json'})
            .done(build_callback(element,feature_type,feature_id));
        }
    }
}

window.onload = initialize_elements;

function update_response(feature_type,feature_id,value)
{
    var jqxhr = $.ajax({
        url:survey_server_url+'/update_response/'+survey_key+'/'+feature_type+'/'+feature_id+(session_key ? '?session_key='+session_key: ''),
        data:{'value':value},
        type:'POST',
	cache: false,
        dataType:'json'})
        .done(function(data) {
        if (data['status'] = 200)
        {
            $("#"+feature_type+"_"+feature_id).html(data['html']);
            initialize_feature(feature_type,feature_id,data['value']);
        }
    }
    )
}

function update_field(feature_type,feature_id)
{
    var attributes =$('#'+feature_type+'_'+feature_id+'_form').serialize();
    $('#'+feature_type+'_'+feature_id+'_modal').modal('hide').on('hidden.bs.modal', function(){
        var jqxhr = $.ajax({
            url:survey_server_url+'/update_field/'+survey_key+'/'+feature_type+'/'+feature_id,
            data:{'attributes':attributes},
            type:'POST',
	    cache: false,
            dataType:'json'})
            .done(function(data) {
                if (data['status'] = 200)
                {
                    $("#"+feature_type+"_"+feature_id).html(data['html']);
                    initialize_feature(feature_type,feature_id,data['value']);
               }
            });
        }
    );
}

/*helper functions for the rate element */

function mouseover_star(feature_id,star,current_value)
{
    for(var i=1;i<=5;i++)
    {
        var e = $('#rate_'+feature_id+'_'+i);
        if (i <= star)
        {
            if(! e.hasClass('yellow'))
                e.addClass('yellow');
        }
        else
        {
            if(e.hasClass('yellow'))
                e.removeClass('yellow');
        }
    }
}

function init_slider_value(feature_id,value)
{
    scale = document.getElementById('scale_'+feature_id+'_gradient');
    slider = document.getElementById('scale_'+feature_id+'_slider');
    var total_width = scale.offsetWidth;
    var slider_position = (value+1.0)/2.0*total_width;
    slider.style.left = Math.floor(slider_position-slider.offsetWidth/2.0)+"px";
}

function update_slider_value(e,feature_id)
{
    scale = document.getElementById('scale_'+feature_id+'_gradient');
    slider = document.getElementById('scale_'+feature_id+'_slider');
    var offset_x = scale.offsetLeft;
    var total_width = scale.offsetWidth;
    var mouse_x = e.clientX-offset_x;
    var value = mouse_x/total_width*2.0-1.0;
    update_response('scale',feature_id,value);
}

function move_slider_value(e,feature_id)
{
    scale = document.getElementById('scale_'+feature_id+'_gradient');
    slider = document.getElementById('scale_'+feature_id+'_slider');
    var offset_x = scale.offsetLeft;
    var total_width = scale.offsetWidth;
    var mouse_x = e.clientX-offset_x;
    slider.style.left = Math.floor(mouse_x-slider.offsetWidth/2.0)+"px";
}

function mouseout_star(feature_id,star,current_value)
{
    for(var i=1;i<=5;i++)
    {
        var e = $('#rate_'+feature_id+'_'+i);
        if (i <= current_value)
        {
            if(! e.hasClass('yellow'))
                e.addClass('yellow');
        }
        else
        {
            if(e.hasClass('yellow'))
                e.removeClass('yellow');
        }
    }
}