
var feature_types = ['vote','input','rate'];
var admin = '';
var survey_key = null;
var survey_server_url = '';

function initialize_feature(feature_type,feature_id)
{
    if (feature_type == 'input' || feature_type == 'rate')
    {
        $(function(){
        $('[rel=popover]').popover({ 
        html : true, 
        content: function() {
        return $('#popover_content_wrapper').html();
        }
        });
        });
    }
}

function initialize_elements()
{
    if (! survey_key)
    {
        alert("survey key undefined!");
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
                        initialize_feature(feature_type,feature_id);
                    }
                }            
            };
            var jqxhr = $.ajax({
            url:survey_server_url+'/get_html/'+survey_key+'/'+feature_type+'/'+feature_id+(admin ? '?admin='+admin : ''),
            data:{},
            type:'GET',
            dataType:'json'})
            .done(build_callback(element,feature_type,feature_id));
        }
    }
}

function update_response(feature_type,feature_id,value)
{
    document.getElementById("status_info").innerHTML = "Syncing..."
    var jqxhr = $.ajax({
        url:survey_server_url+'/update_response/'+survey_key+'/'+feature_type+'/'+feature_id,
        data:{'value':value},
        type:'POST',
        dataType:'json'})
        .done(function(data) {
        if (data['status'] = 200)
        {
            document.getElementById("status_info").innerHTML = "Saved.";
            setTimeout(function() { document.getElementById("status_info").innerHTML = "";}, 2000);
            $("#"+feature_type+"_"+feature_id).html(data['html']);
        }
    }
    )

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

function mouseout_star(feature_id,star,current_value)
{
    for(var i=1;i<=5;i++)
    {
        var e = $('#rate_'+feature_id+'_'+i);
        if(e.hasClass('yellow') & i > current_value)
            e.removeClass('yellow');
    }
}