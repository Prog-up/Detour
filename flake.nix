{
  description = "Détour development environment";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python3
            python3Packages.pygobject3
            python3Packages.pycairo
            python3Packages.pillow
            gtk4
            libadwaita
            gobject-introspection
            ninja
            meson
            pkg-config
            desktop-file-utils
            appstream
            appstream-glib
            flatpak
            flatpak-builder
            gdk-pixbuf
            librsvg
            gsettings-desktop-schemas
          ];
          shellHook = ''
            export GI_TYPELIB_PATH="${pkgs.libadwaita}/lib/girepository-1.0:${pkgs.gtk4}/lib/girepository-1.0:${pkgs.gobject-introspection}/lib/girepository-1.0:$GI_TYPELIB_PATH"
            export XDG_DATA_DIRS="${pkgs.gsettings-desktop-schemas}/share/gsettings-schemas/${pkgs.gsettings-desktop-schemas.name}:${pkgs.gtk4}/share-gsettings-schemas/${pkgs.gtk4.name}:${pkgs.libadwaita}/share:$XDG_DATA_DIRS"
            echo "Détour GNOME / GTK4 Dev Shell Activated!"
          '';
        };
      }
    );
}
