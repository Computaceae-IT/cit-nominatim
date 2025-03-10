// You can overwrite any defaults in dist/theme/config.theme.js

let Nominatim_Config = {
  Page_Title: 'CIT-Nominatim',

  // Where Nominatim API runs. Remember to add port if needed and trailing slash.
  Nominatim_API_Endpoint: 'http://nominatim.computaceae-it.tech/api/',

  // relative path or full URL
  Images_Base_Url: 'mapicons/',

  // If the API should return polygons to be displayed on the map
  Search_AreaPolygons: true,

  // ---- MAP ----
  Reverse_Default_Search_Zoom: 18,
  Map_Default_Lat: 47.0983865,
  Map_Default_Lon: 6.8271777,
  Map_Default_Zoom: 15,

  // For what {x}, {y} etc stand for see
  // https://leafletjs.com/reference-1.6.0.html#tilelayer
  Map_Tile_URL: 'https://{s}.tile.osm.org/{z}/{x}/{y}.png',

  // Can be text or HTML. To hide set to ''
  Map_Tile_Attribution: '<a href="https://osm.org/copyright">OpenStreetMap contributors</a>'
};
