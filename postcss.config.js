module.exports = ({options}) => ({
    plugins: [
        require('autoprefixer'),
        require('postcss-url')(options.postCSSURLOptions || {})
    ]
});
