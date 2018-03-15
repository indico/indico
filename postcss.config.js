module.exports = ({options}) => ({
    plugins: [
        require('autoprefixer'),
        require('postcss-url-namespaces')(options.urlnamespaces || {})
    ]
});
