#include <stdlib.h>

#include "my_application.h"

// Impeller (backend de rendu par défaut de Flutter sur Linux) fait planter le
// thread raster du moteur à la destruction d'une texture externe :
//
//   io.flutter.rast[…]: segfault at 0 … in libflutter_linux_gtk.so
//
// `media_kit` affichant la vidéo via une texture externe, l'application meurt
// dès qu'on quitte le lecteur. On force donc le backend historique tant que le
// défaut n'est pas corrigé en amont ; voir la section « Lecture vidéo sur
// Linux » du README. Supprimer ce bloc pour repasser sur Impeller.
//
// `setenv(..., 0)` : un réglage passé depuis l'extérieur (ou par
// `flutter run --enable-impeller`) reste prioritaire.
static void disable_impeller() {
  setenv("FLUTTER_ENGINE_SWITCHES", "1", 0);
  setenv("FLUTTER_ENGINE_SWITCH_1", "enable-impeller=false", 0);
}

int main(int argc, char** argv) {
  disable_impeller();

  g_autoptr(MyApplication) app = my_application_new();
  return g_application_run(G_APPLICATION(app), argc, argv);
}
