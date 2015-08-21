(function(global) {
    'use strict';

    $(document).ready(function(){
        Dropzone.autoDiscover = false;
    });

    global.setupDropzone = function(element) {
        var $dz = $(element),
            $form = $dz.closest('form'),
            $flashArea = $form.find('.flashed-messages'),
            options = {
                clickable: element + ' .dropzone-inner',
                previewsContainer: element + ' .dropzone-previews',
                autoProcessQueue: false,

                init: function() {
                    var $button = $form.find('input[type="submit"], .js-dropzone-upload'),
                        self = this,
                        file = $dz.data('value');

                    if (file) {
                        var existingFile = {
                            name: file.filename,
                            size: file.size,
                            accepted: true
                        };

                        self.emit('addedfile', existingFile);
                        $dz.find('.dz-progress').hide();
                        self.files[0] = existingFile;

                        /* Disable opening the upload dialog when clicking on the file's preview element */
                        $dz.find('.dz-preview').on('click', function(e) {
                            e.stopPropagation();
                        });

                        // Check if the existing file is an image and add the image preview.
                        if (file.content_type.match(/image\/.*/) && file.url) {
                            $dz.find('.dz-image > img').attr('src', file.url);
                            $dz.find('.dz-image > img').attr('width', '120px');
                            $dz.find('.dz-preview').removeClass('dz-file-preview').addClass('dz-image-preview');
                        }
                    }

                    $button.on('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        $button.prop('disabled', true);

                        if (self.getQueuedFiles().length) {
                            $dz.find('.dz-progress').show();
                            self.processQueue();
                        } else {
                            $form.submit();
                        }
                    });

                    self.on('addedfile', function(file) {
                        if (!options.uploadMultiple && self.files.length > 1) {
                            self.removeFile(self.files[0]);
                        }

                        // force change in form, so that we can process
                        // the 'change' event
                        $button.prop('disabled', false);
                        $form.find('.change-trigger').val('2');
                        $form.trigger('change');

                        $dz.find('.dz-message').hide();
                        $dz.find('.dz-progress').hide();
                        $(file.previewElement).on('click', function(e) {
                            e.stopPropagation();
                        });
                    });

                    self.on('removedfile', function(file) {

                        $button.prop('disabled', false);
                        // force change in form, so that we can process
                        // the 'change' event
                        $form.find('.change-trigger').val('0');
                        $form.trigger('change');

                        if (self.files.length === 0) {
                            $dz.find('.dz-message').show();
                        }
                    });

                    self.on('sendingmultiple', function() {
                        $form.trigger('ajaxDialog:beforeSubmit');
                    });

                    self.on('success', function(e, response) {
                        if (options.submitForm) {
                            $form.submit();
                        }
                        if (options.handleFlashes) {
                            handleFlashes(response, true, $flashArea);
                        }

                        $dz.data('value', response.content);
                        $form.find('.change-trigger').val($dz.data('value') ? '1' : '0');
                        $form.trigger('indico:fieldsSaved', response);
                        $form.trigger('ajaxDialog:success', [response]);
                    });

                    self.on('error', function(e, msg, xhr) {
                        if (xhr) {
                            $form.trigger('ajaxDialog:error', [xhr]);
                        }
                    });
                }
            };

        _.extend(options, $dz.data('options'));
        var param = options.paramName;
        options.paramName = function() { return param; };

        // include the csrf token in case the dropzone is submitting data to a
        // seperate endpoint than the form's action
        if (options.url) {
            options.params = {
                'csrf_token': $form.find('#csrf_token').val()
            };
            $dz.dropzone(options);
        }
        else {
            $form.dropzone(options);
        }
    };

})(window);
