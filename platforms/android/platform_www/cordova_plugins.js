cordova.define('cordova/plugin_list', function(require, exports, module) {
  module.exports = [
    {
      "id": "cordova-plugin-applovin-max.AppLovinMAX",
      "file": "plugins/cordova-plugin-applovin-max/www/applovinmax.js",
      "pluginId": "cordova-plugin-applovin-max",
      "clobbers": [
        "applovin"
      ]
    },
    {
      "id": "cordova-plugin-googleplus.GooglePlus",
      "file": "plugins/cordova-plugin-googleplus/www/GooglePlus.js",
      "pluginId": "cordova-plugin-googleplus",
      "clobbers": [
        "window.plugins.googleplus"
      ]
    }
  ];
  module.exports.metadata = {
    "cordova-plugin-applovin-max": "2.1.0",
    "cordova-plugin-googleplus": "8.5.2"
  };
});