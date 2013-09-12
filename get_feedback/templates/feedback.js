
function vote_links(feature_id,status)
{
    up_html = "<a href=\"/upvote/"+feature_id+"\" onclick=\"upvote_feature('"+feature_id+"');return false;\"><i class=\"icon-thumbs-up icon-2x\"></i></a>"
    down_html = "<a href=\"/downvote/"+feature_id+"\" onclick=\"downvote_feature('"+feature_id+"');return false;\"><i class=\"icon-thumbs-down icon-2x\"></i></a>"
    if (status == 'upvoted')
    {
        up_html = "<a href=\"/undo_upvote/"+feature_id+"\" onclick=\"undo_upvote_feature('"+feature_id+"');return false;\"><i class=\"icon-chevron-up icon-2x green\"></i></a>"
    }
    else if (status == 'downvoted')
    {
        down_html = "<a href=\"/undo_downvote/"+feature_id+"\" onclick=\"undo_downvote_feature('"+feature_id+"');return false;\"><i class=\"icon-chevron-down icon-2x red\"></i></a>"
    }
    return up_html+down_html
}

function upvote_feature(feature_id,up)
{

    var jqxhr = $.ajax({
        url:"/upvote_feature/"+feature_id,
        data:{},
        type:'GET',
        dataType:'json'})
        .done(function(data) {
        if (data['status'] = 200)
        {
            $("#feature-"+feature_id).html(vote_links(feature_id,'upvoted'));
        }
    }
    )
}

function undo_upvote_feature(feature_id)
{
    var jqxhr = $.ajax({
        url:"/undo_upvote/"+feature_id,
        data:{},
        type:'GET',
        dataType:'json'})
    .done(function(data) {
        if (data['status'] = 200)
        {
            $("#feature-"+feature_id).html(vote_links(feature_id,'neutral'));
        }
    }
    )
}

function downvote_feature(feature_id,up)
{

    var jqxhr = $.ajax({
        url:"/downvote/"+feature_id,
        data:{},
        type:'GET',
        dataType:'json'})
        .done(function(data) {
        if (data['status'] = 200)
        {
            $("#feature-"+feature_id).html(vote_links(feature_id,'downvoted'));
        }
    }
    )
}

function undo_downvote_feature(feature_id)
{
    var jqxhr = $.ajax({
        url:"/undo_downvote/"+feature_id,
        data:{},
        type:'GET',
        dataType:'json'})
    .done(function(data) {
        if (data['status'] = 200)
        {
            $("#feature-"+feature_id).html(vote_links(feature_id,'neutral'));
        }
    }
    )
}
