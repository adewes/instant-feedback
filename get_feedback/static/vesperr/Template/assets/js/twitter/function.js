$(document).ready(function() { 
$(".tweet").tweet({
	 username: "wrapbootstrap",
	 join_text: null,
	 avatar_size: null,
	 count:1,
	 auto_join_text_default: "we said,", 
	 auto_join_text_ed: "we",
	 auto_join_text_ing: "we were",
	 auto_join_text_reply: "we replied to",
	 auto_join_text_url: "we were checking out",
	 loading_text: "loading tweets..."
 });
});
