function GoogleDocumentEditBlock(runtime, element) {
    var clear_name_button = $('.clear-display-name', element);
    var save_button = $('.save-button', element);
    var validation_alert = $('.validation_alert', element);
    var embed_code_textbox = $('#edit_embed_code', element);
    var xblock_inputs_wrapper = $('.xblock-inputs', element);
    var edit_display_name_input = $('#edit_display_name', element);
    var error_message_div = $('.xblock-editor-error-message', element);
    var defaultName = edit_display_name_input.attr('data-default-value');
    var edit_alt_text_input = $('#edit_alt_text', element);
    var alt_text_item = $('li#alt_text_item', element);

    var LibhandlerUrl = runtime.handlerUrl(element, 'source_library_values');
    var ProbhandlerUrl = runtime.handlerUrl(element, 'source_problem_values');

    var library_options = [];

    toggleClearDefaultName();
    loadData();

    save_button.bind('click', SaveEditing);
    function addLibraries(result) {
        library_options = result;
        setLibraryOption(result);
    }

    function setLibraryOption(data){

        var initial = $("#library_options").val();
        var match =false;
        $("#library_options").empty();
        $.each(data, function(index, option){

            if (option.value == initial){
                match =true;
            }

            $("#library_options").append($('<option>', {
                value: option.value,
                text: option.display_name
            }))
            });
        if (match ){
        $("#library_options").val(initial);
          $.ajax({
                type: "POST",
                url: ProbhandlerUrl,
                data: JSON.stringify({"source_library_id": initial}),
                success: addProblems
            });
        }
    }

    function addProblems(result) {
        var element = $("#problem_options");
        var initial = element.val();
        var match =false;
        element.empty();
        $.each(result, function(index, option){
             if (option.value == initial){
                match =true;
            }
            element.append($('<option>', {
                value: option.value,
                text: option.display_name
            }))
        });
        if (match ){
          element.val(initial);
      }
        toggleClearOptions(element, '.clear-problem');
    }

    $("#library_options").change(function(){
        var element = $("#problem_options");
        var value = $("option:selected", this).val();
        if(value != ""){
            $.ajax({
                type: "POST",
                url: ProbhandlerUrl,
                data: JSON.stringify({"source_library_id": value}),
                success: addProblems
            });
            element.prop('disabled', false);
            toggleClearOptions($(this), $('.clear-library'));
        } else {
            element.prop('disabled', true);
            element.empty();
            toggleClearOptions($(this), $('.clear-library'));
        }
    })

    $("#problem_options").change(function(){
        toggleClearOptions($(this), $('.clear-problem'));
    })

    $('.clear-display-name', element).bind('click', function() {
        $(this).addClass('inactive');
        edit_display_name_input.val(defaultName);
    });

    $('.clear-library', element).bind('click', function() {
        $(this).addClass('inactive');
        setLibraryOption(library_options);
    });

    $('.clear-problem', element).bind('click', function() {
        $(this).addClass('inactive');
        $("#problem_options").prop('disabled', true);
        $("#problem_options").empty();
    });

    edit_display_name_input.bind('keyup', function(){
        toggleClearDefaultName();
    });

    /*($('#edit_embed_code', element).bind('keyup', function(){
        IsUrlValid();
    });*/

    $('.cancel-button', element).bind('click', function() {
        runtime.notify('cancel', {});
    });

    function loadData(){
        console.log("loaddata")
        $.ajax({
            type: "POST",
            url: LibhandlerUrl,
            data: JSON.stringify({"hello": "world"}),
            success: addLibraries
        });
    }

    function toggleClearDefaultName(){
        if (edit_display_name_input.val() == defaultName || edit_display_name_input.val() == ""){
            if (!clear_name_button.hasClass('inactive')){
                clear_name_button.addClass('inactive');
            }
        } else {
            clear_name_button.removeClass('inactive');
        }
    }

    function toggleClearOptions(element, clear_button){
        console.log(element)
        console.log(element.children().size())
        if ($("option:selected", element).val() == ""){
            clear_button.addClass('inactive');
        } else {
            clear_button.removeClass('inactive');
        }
    }

    function SaveEditing(){
        var data = {
            'display_name': edit_display_name_input.val(),
            'library': $("#library_options").children("option:selected").val(),
            'problem': $("#problem_options").children("option:selected").val(),
            'test': "i am therere"
        };
        console.log(data);

        error_message_div.html();
        error_message_div.css('display', 'none');

        var handlerUrl = runtime.handlerUrl(element, 'studio_submit');
        $.post(handlerUrl, JSON.stringify(data)).done(function(response) {

            if (response.result === 'success') {
                window.location.reload(false);
            } else {
                error_message_div.html('Error: '+response.message);
                error_message_div.css('display', 'block');
            }
        });
    }
    /*
    function HideAltTextInput(){
        edit_alt_text_input.val('');
        alt_text_item.addClass('covered');
    }

    function IsUrlValid(){
        var embed_html = embed_code_textbox.val();

        var google_doc = $(embed_html);
        embed_code_textbox.css({'cursor':'wait'});
        save_button.addClass('disabled').unbind('click');

        $.ajax({
            type: "POST",
            url: runtime.handlerUrl(element, 'check_url'),
            data: JSON.stringify({url: google_doc.attr("src")}),
            success: function(result) {
                if (result.status_code >= 400){
                    validation_alert.removeClass('covered');
                    embed_code_textbox.addClass('error');
                    xblock_inputs_wrapper.addClass('alerted');
                    HideAltTextInput();
                } else {
                    validation_alert.addClass('covered');
                    save_button.removeClass('disabled');
                    embed_code_textbox.removeClass('error');
                    xblock_inputs_wrapper.removeClass('alerted');

                    save_button.bind('click', SaveEditing);

                    if (embed_html.toLowerCase().indexOf("<img") >= 0){
                        if (alt_text_item.hasClass('covered')){
                            alt_text_item.removeClass('covered');
                        }
                    } else {
                        if (!alt_text_item.hasClass('covered')){
                            HideAltTextInput();
                        }
                    }
                }
            },
            error: function(result) {
                validation_alert.removeClass('covered');
                save_button.addClass('disabled').unbind('click');
                embed_code_textbox.addClass('error');
                xblock_inputs_wrapper.addClass('alerted');
            },
            complete: function() {
                embed_code_textbox.css({'cursor':'auto'});
            }
        });
    }*/
}
