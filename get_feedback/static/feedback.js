
var field_types = ['vote','input','rate','scale','check','select'];
var survey_key = null;
var response_key = getParameterByName('response_key');
var show_summary = getParameterByName('show_summary');
var survey_url = document.URL;
var survey_server_url = '';
var select_element = false;
var show_menu = true;
var selected_element_path = null;
var dynamic_fields = []
var allowed_elements = ['DIV','P','H1','H2','H3','H4','H5','H6','LI','TD','TH'];

$(document).ready(function() {
        jQuery.support.cors = true;
        window.onmessage = handle_message;
        if (survey_key)
        {
            initialize_survey();
        }
        }); 

function handle_message(e)
{
    e = e || window.event;
    var data = eval(JSON.parse(e.data));
    if (data['type'] == 'reload_field')
    {
        $.fancybox.close();
        reload_field(data['field_type'],data['field_id'])
    }
    else if (data['type'] == 'toggle_results')
    {
        show_summary = ! show_summary;
        initialize_survey();
    }
    else if (data['type'] == 'select_element')
    {
        select_element = true;
    }
    else if (data['type'] == 'get_selected_element_path')
    {
        var post_data={'type':'selected_element_path','path':selected_element_path};
        e.source.postMessage(JSON.stringify(post_data),'*');
    }
}


function getParameterByName(name) {
    name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
        results = regex.exec(location.search);
    return results == null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
}


function get_element_for_field(field_type,field_id)
{
    var element = $('span.survey_'+field_type+'#'+field_id);
    if (element.length)
        element.addClass("survey_field");
    return element;
}

function autodiscover_fields()
{
    var discovered_fields = []
    for(var i=0;i<field_types.length;i++)
    {
        var field_type = field_types[i];
        var fields = $('.survey_'+field_type);
        for (var j=0;j<fields.length;j++)
        {
            var field = $(fields[j]);
            var field_id = field.attr('id');
            discovered_fields.push([field_type,field_id]);
        }  
    }
    return discovered_fields;
}

function initialize_fields(fields)
{
    var known_fields = [];
    for(var field_type in fields)
    {
        for(var field_id in fields[field_type])
        {
            var field = fields[field_type][field_id];
            known_fields.push([field_type,field_id]);
            element = get_element_for_field(field_type,field_id)
            if (element != undefined)
            {
                element.html(field['html']);
            }
        }
    }
    return known_fields;
}

function autocreate_fields(fields)
{
    var jqxhr = $.ajax({
    url:survey_server_url+'/autocreate_fields/'+survey_key+'?show_summary='+(show_summary ? '1' : '')+(response_key ? '&response_key='+response_key: ''),
    cache: false,
    data : {'fields':JSON.stringify(fields)},
    xhrFields: {withCredentials: true},
    type:'POST',
    success:function(data) {
            if (data['status'] = 200)
            {
                var fields = data['survey_parameters']['fields'];
                initialize_fields(fields);
            }
        }    
    })
}

function initialize_survey()
{

    $(".survey").fancybox({
    maxWidth    : 600,
    maxHeight   : 600,
    fitToView   : false,
    autoSize    : false,
    closeClick  : false,
    openEffect  : 'none',
    closeEffect : 'none'
    });

    var discovered_fields = autodiscover_fields();

    var jqxhr = $.ajax({
    url:survey_server_url+'/initialize_survey/'+survey_key+'?show_summary='+(show_summary ? '1' : '')+(response_key ? '&response_key='+response_key: ''),
    cache: false,
    xhrFields: {withCredentials: true},
    type:'POST',
    success:function(data) {
            if (data['status'] = 200)
            {
                var fields = data['survey_parameters']['fields'];
                response_key = data['survey_parameters']['response_key'];
                known_fields = initialize_fields(fields);
                if (data['survey_parameters']['admin'])
                {
                    var new_fields = [];
                    for(var i in discovered_fields)
                    {
                        if (known_fields.indexOf(discovered_fields[i]) == -1)
                            new_fields.push(discovered_fields[i]);
                    }
                    if (new_fields.length)
                    {
                        autocreate_fields(new_fields);
                    }
                    if (show_menu)
                        initialize_menu();
                }
            }
            }    
        })   
}

function initialize_menu()
{
    if (!survey_key)
        return;
    function adapt_body_margin()
    {
        $('body').css("margin-top",($('#survey_menu').height()+40)+'px');
    }
    $('body').prepend('<iframe scrolling="no" id="survey_menu" src="'+survey_server_url+'/survey_menu/'+survey_key+'"></iframe>');
    $('html').css('position','absolute');
    $('html').css('width','100%');
    $('html').css('top',($('#survey_menu').height())+'px');
}

function reload_field(field_type,field_id)
{
    var jqxhr = $.ajax({
    url:survey_server_url+(show_summary ? '/view_summary_inline/' : '/view_field_inline/')+survey_key+'/'+field_type+'/'+field_id+(response_key ? '?response_key='+response_key: ''),
    data:{},
    cache: false,
    type:'GET',
    xhrFields: {withCredentials: true},
    dataType:'jsonp',
    success:
        function(data) {
            if (data['status'] = 200)
            {
                var element = get_element_for_field(field_type,field_id);
                element.html(data['html']);
            }
        }          
    })
}

function update_response(field_type,field_id,value)
{
    var jqxhr = $.ajax({
        url:survey_server_url+'/update_response/'+survey_key+'/'+field_type+'/'+field_id+(response_key ? '?response_key='+response_key: ''),
        data:{'value':value,'url':survey_url},
        type:'GET',
    	cache: false,
        xhrFields: {withCredentials: true},
        dataType:'jsonp',
        success:function(data) {
        if (data['status'] = 200)
        {
            var element = get_element_for_field(field_type,field_id,{});
            element.html(data['html']);
        }
    }

    });
}

/*helper functions for the rate field */

function mouseover_star(field_id,star,current_value)
{
    var i=1;
    while(true)
    {
        var e = $('#rate_'+field_id+'_'+i);
        if (!e.length)
            break;
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
        i++;
    }
}

function mouseout_star(field_id,star,current_value)
{
    var i = 1;
    while(true)
    {
        var e = $('#rate_'+field_id+'_'+i);
        if (!e.length)
            break;
        var e = $('#rate_'+field_id+'_'+i);
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
        i++;
    }
}
