const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const Dotenv = require("dotenv-webpack");

module.exports = {
    entry: "./src/index.jsx",
    output: {
        path: path.join(__dirname, "../dist"),
        filename: "static/js/bundle.js",
        publicPath: "/static/",
    },
    resolve: {
        extensions: [".jsx", ".js"],
    },
    module: {
        rules: [
            {
                test: /\.(jsx|js)$/,
                exclude: /node_modules/,
                use: {
                    loader: 'babel-loader',
                    options: {
                        presets: [
                            ['@babel/preset-env', {
                                "targets": {
                                    "browsers": ["last 2 versions"]
                                }
                            }],
                            ['@babel/preset-react']
                        ]
                    }
                }
            },
            {
                test: /\.css$/,
                use: ["style-loader", "css-loader"],
            },
            {
                test: /\.(png|jpe?g|gif|svg)$/i,
                type: 'asset/resource',
                generator: {
                    filename: 'static/images/[name][ext][query]'
                }
            },
        ]
    },
    plugins: [
        new HtmlWebpackPlugin({
            template: "./src/index.html",
            filename: "index.html"
        }),
        new Dotenv({
            path: './.env',
            systemvars: true,
        })
    ],
    devServer: {
        static: {
            directory: path.join(__dirname, "../dist"),
        },
        compress: true,
        port: 3000,
        historyApiFallback: true,
        hot: true
    }
};