(function(global) {
    'use strict';

    $(document).ready(function(){
        Dropzone.autoDiscover = false;
    });


    global.setupDropzone = function() {
        $('.dropzone').each(function() {
            var $form = $(this),
                $area = $form.find('.dropzone-area'),
                options = {
                    clickable: '.dropzone-area',
                    previewsContainer: '.dropzone-previews',
                    autoProcessQueue: false,

                    init: function() {
                        var $button = $form.find('input[type="submit"], .js-dropzone-upload'),
                            self = this,
                            file = $area.data('value');

                        if (file) {
                            var existingFile = {
                                name: file.file_name,
                                size: file.size,
                                accepted: true
                            };

                            self.emit('addedfile', existingFile);
                            $('.dz-progress').hide();
                            self.files[0] = existingFile;

                            /* Disable opening the upload dialog when clicking on the file's preview element */
                            $('.dz-preview').on('click', function(e) {
                                e.stopPropagation();
                            });

                            // Check if the existing file is an image and add the image preview.
                            if (file.content_type.match(/image\/.*/) && file.url) {
                                $('.dz-image > img').attr('src', file.url);
                                $('.dz-image > img').attr('width', '120px');
                                $('.dz-preview').removeClass('dz-file-preview').addClass('dz-image-preview');
                            }
                        }

                        $button.on('click', function(e) {
                            e.preventDefault();
                            e.stopPropagation();
                            $button.prop('disabled', true);

                            if (self.getQueuedFiles().length) {
                                $('.dz-progress').show();
                                self.processQueue();
                            }
                            else {
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
                            $form.find('.change-trigger').val(self.files.length);
                            $form.trigger('change');

                            $('.dz-message').hide();
                            $('.dz-progress').hide();
                            $(file.previewElement).on('click', function(e) {
                                e.stopPropagation();
                            });
                        });

                        self.on('removedfile', function(file) {

                            // force change in form, so that we can process
                            // the 'change' event
                            $form.find('.change-trigger').val(self.files.length);
                            $form.trigger('change');

                            if (self.files.length === 0) {
                                $('.dz-message').show();
                            }
                        });

                        self.on('sendingmultiple', function() {
                            $form.trigger('ajaxDialog:beforeSubmit');
                        });

                        self.on('success', function(e, response) {
                            if (options.submit_form) {
                                $form.submit();
                            }
                            $form.trigger('ajaxDialog:success', [response]);
                        });

                        self.on('error', function(e, msg, xhr) {
                            if (xhr) {
                                $form.trigger('ajaxDialog:error', [xhr]);
                            }
                        });
                    }
                };

            _.extend(options, $area.data('options'));
            var param = options.paramName;
            options.paramName = function() { return param; };

            $form.dropzone(options);

        });
    };

})(window);
