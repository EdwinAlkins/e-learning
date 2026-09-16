import 'package:flutter_riverpod/flutter_riverpod.dart';

class CurrentUid extends Notifier<String?> {
  @override
  String? build() => null;

  void setUid(String? uid) => state = uid;
}

final currentUidProvider = NotifierProvider<CurrentUid, String?>(
  CurrentUid.new,
);
