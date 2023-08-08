const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const webpack = require('webpack');

module.exports = (env, argv) => {
    const devtool = argv.mode === "production" ? "eval-source-map" : "inline-source-map"
    
    return {
        entry: {
            scripts: './src/index.js',
            styles: './src/styles/style.scss'
        },
        output: {
            path: path.join(__dirname, '/dist'),
            filename: '[name].[fullhash].js'
        },
        devtool: devtool,
        module: {
            rules: [
                {
                    test: /\.(js|jsx)$/,
                    enforce: 'pre',
                    exclude: /node_modules/,
                    use: {
                        loader: 'babel-loader',
                    }
                },
                {
                    test: /\.css$/i,
                    use: [
                        'style-loader',
                        'css-loader',
                    ]
                },
                {
                    test: /\.s[ac]ss$/i,
                    use: [
                        'style-loader',
                        'css-loader',
                        'sass-loader',
                    ],
                },
                {
                    test: /\.pem$/i,
                    use: 'raw-loader',
                },
                {
                    test: /\.(ttf|eot|woff|woff2|otf)$/,
                    use: {
                        loader: "file-loader",
                        options: {
                            name: "fonts/[name].[ext]",
                        },
                    },
                },
            ]
        },
        plugins: [
            new HtmlWebpackPlugin({
                template: 'src/index.html',
                favicon: "src/static/favicon.png"
            }),
            new CleanWebpackPlugin(),
            new webpack.EnvironmentPlugin({
                BACKEND_URL: env.production ? 
                    'https://testbed-manager.mysmce.com/api/' : env.development ? 
                    'http://127.0.0.1:5000/' : 'http://127.0.0.1/api/'
            }),
            new webpack.ProvidePlugin({
                Buffer: ['buffer', 'Buffer'],
                process: 'process/browser'
            })
        ],
        devServer: {
            inline: true,
            port: 8000,
            historyApiFallback: true
        },
        resolve: {
            extensions: ['.js', '.jsx'],
        }
    }
}