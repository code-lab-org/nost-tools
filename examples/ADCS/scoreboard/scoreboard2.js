// Grant CesiumJS access to your ion assets
Cesium.Ion.defaultAccessToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJkMDYyZWI5YS0wZDMyLTQxZjUtOTkxZi04NzkyMzM0YTZiYzAiLCJpZCI6OTA2NTQsImlhdCI6MTY1MDQ5Mzk1OH0.uWM48K-hD7eA-cU7Wo6Z3Pyp_0SntGeoi0mw5eo0Xd8";

const viewer = new Cesium.Viewer("cesiumContainer", {
  terrainProvider: new Cesium.CesiumTerrainProvider({
    url: Cesium.IonResource.fromAssetId(1),
  }),
});
viewer.scene.globe.depthTestAgainstTerrain = true;

const tileset = viewer.scene.primitives.add(
  new Cesium.Cesium3DTileset({
    url: Cesium.IonResource.fromAssetId(1595223),
  })
);

(async () => {
  try {
    await tileset.readyPromise;
    await viewer.zoomTo(tileset);

    // Apply the default style if it exists
    const extras = tileset.asset.extras;
    if (
      Cesium.defined(extras) &&
      Cesium.defined(extras.ion) &&
      Cesium.defined(extras.ion.defaultStyle)
    ) {
      tileset.style = new Cesium.Cesium3DTileStyle(extras.ion.defaultStyle);
    }
  } catch (error) {
    console.log(error);
  }
})();
