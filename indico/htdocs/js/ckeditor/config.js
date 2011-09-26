/*
Copyright (c) 2003-2011, CKSource - Frederico Knabben. All rights reserved.
For licensing, see LICENSE.html or http://ckeditor.com/license
*/

CKEDITOR.editorConfig = function( config )
{
    config.toolbar = 'IndicoMinimal';

    config.toolbar_IndicoFull =
    [
        ['Source','-','Preview','Templates'],
        ['Cut','Copy','Paste','PasteText','PasteFromWord','-','Print', 'SpellChecker', 'Scayt'],
        ['Undo','Redo','-','Find','Replace','-','SelectAll','RemoveFormat'],
        ['Bold','Italic','Underline','Strike','-','Subscript','Superscript'],
        ['NumberedList','BulletedList','-','Outdent','Indent','Blockquote','CreateDiv'],
        ['JustifyLeft','JustifyCenter','JustifyRight','JustifyBlock'],
        ['Link','Unlink','Anchor'],
        ['Image','Table','HorizontalRule','Smiley','SpecialChar','PageBreak'],
        '/',
        ['Styles','Format','Font','FontSize'],
        ['TextColor','BGColor'],
        ['Maximize', 'ShowBlocks','-','About']
    ];

    config.toolbar_IndicoMinimal =
     [
        ['Source','-','Preview','Templates'],
         ['Bold','Italic','Underline','StrikeThrough','-','Subscript','Superscript','-'],
         ['Outdent', 'Indent', '-', 'NumberedList','BulletedList','Blockquote','-','Link','Unlink','Anchor'],
         ['JustifyLeft','JustifyCenter','JustifyRight','JustifyFull'],
         ['SpecialChar','-','About']
     ] ;

    config.contentsCss = CKEDITOR.basePath + '../../css/Default.css';

    config.resize_enabled = false;

    config.toolbarStartupExpanded = true;

    config.toolbarCanCollapse = false;

    //url int angle brackets
    config.protectedSource.push(/<[^<>\s]+:\/\/[^<>\s]+>/g);

    //email address in angle brackets
    config.protectedSource.push(/<[^<>=]+@[^<>]+>/g);

    //done to avoid wrapping paragraphs with <p></p> tags
    config.enterMode = CKEDITOR.ENTER_BR
};
